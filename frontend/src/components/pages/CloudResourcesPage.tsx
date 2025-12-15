import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { useCompartments, useAllResources, cloudApi } from '../../services/cloudService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { PremiumHero } from '../ui/PremiumHero';
import { GlassStatCard } from '../ui/GlassStatCard';

// -- Utility Functions for Intelligence Layer --

// Shape to estimated monthly cost mapping (OCI PAYG approximate pricing)
// NOTE: These are estimates and will vary by region and actual usage
const SHAPE_COST_MAP: Record<string, number> = {
  // Compute Shapes (per month estimate for PAYG)
  'VM.Standard.E2.1.Micro': 0, // Always Free
  'VM.Standard.E2.1': 8,      // ~$0.01/hr
  'VM.Standard.E2.2': 16,     // ~$0.02/hr
  'VM.Standard.E3.Flex': 15,  // Base for 1 OCPU
  'VM.Standard.E4.Flex': 18,
  'VM.Standard.E5.Flex': 20,
  'VM.Standard.E6.Flex': 22,
  'VM.Standard.A1.Flex': 7,   // ARM is cheaper
  'VM.Standard2.1': 25,
  'VM.Standard2.2': 50,
  'VM.Standard2.4': 100,
  'VM.Standard3.Flex': 20,
  // Default for unknown shapes
  'default': 20,
};

// Database edition to cost mapping (per month per OCPU - PAYG, not license)
// OCI Autonomous DB PAYG is ~$0.02-0.05/hr per OCPU
const DB_COST_MAP: Record<string, number> = {
  'ENTERPRISE_EDITION': 75,    // ~$0.10/hr * 730hrs
  'STANDARD_EDITION': 45,      // ~$0.06/hr * 730hrs
  'ENTERPRISE_EDITION_EXTREME_PERFORMANCE': 110,
  'default': 50,
};

// Calculate days since a date
const getDaysSince = (dateString: string | undefined): number => {
  if (!dateString) return 0;
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

// Get estimated monthly cost for a resource
const getEstimatedCost = (resource: any, type: string): number => {
  if (type === 'Compute') {
    const baseShape = resource.shape?.split('.').slice(0, -1).join('.') || resource.shape;
    let cost = SHAPE_COST_MAP[resource.shape] || SHAPE_COST_MAP[baseShape] || SHAPE_COST_MAP['default'];
    // For flex shapes, add per-OCPU cost
    if (resource.shape?.includes('Flex') && resource.shape_config?.ocpus) {
      cost = 15 * resource.shape_config.ocpus + 20; // $15/OCPU + base
    }
    return cost;
  } else if (type === 'Database') {
    const editionCost = DB_COST_MAP[resource.database_edition] || DB_COST_MAP['default'];
    return editionCost * (resource.cpu_core_count || 1);
  } else if (type === 'Volume' || type === 'Storage') {
    // $0.025 per GB per month
    return Math.round((resource.size_in_gbs || 50) * 0.025);
  } else if (type === 'Load Balancer') {
    // Base LB cost
    return 25;
  } else if (type === 'Cluster') {
    // OKE cluster management + estimated node cost
    return 0; // OKE control plane is free
  }
  return 0;
};

// Determine if resource is a "zombie" (definitely needs cleanup)
// NOTE: We cannot determine "stopped for X days" without time_stopped from OCI API
// So we only flag TERMINATED/DELETED resources as zombies (definite cleanup candidates)
const isZombieResource = (resource: any): boolean => {
  const state = resource.lifecycle_state?.toLowerCase();
  // Only flag TERMINATED or DELETED - these are definite cleanup candidates
  // STOPPED is NOT zombie - could be scheduled maintenance, weekend shutdown, etc.
  return ['terminated', 'deleted'].includes(state);
};

// Get waste indicator
const getWasteInfo = (resource: any, type: string): { isWaste: boolean; reason: string; amount: number } | null => {
  const state = resource.lifecycle_state?.toLowerCase();
  if (state === 'stopped') {
    // Stopped compute still pays for boot volume - BUT this is expected for scheduled shutdowns
    // Only flag if we want users to be aware of boot volume cost
    if (type === 'Compute') {
      return { isWaste: true, reason: 'Boot volume still attached (cost continues)', amount: 10 };
    }
  }
  if (state === 'available' && (type === 'Volume' || type === 'Storage')) {
    // Unattached storage
    return { isWaste: true, reason: 'Unattached storage', amount: getEstimatedCost(resource, type) };
  }
  if (state === 'deleted' && type === 'Cluster') {
    return { isWaste: true, reason: 'Deleted cluster still tracked', amount: 0 };
  }
  return null;
};

// Calculate health score (0-10) for a resource
const getHealthScore = (resource: any, type: string): { score: number; color: string; emoji: string; issues: string[] } => {
  let score = 10;
  const issues: string[] = [];
  const state = resource.lifecycle_state?.toLowerCase();

  // State-based scoring
  if (state === 'running' || state === 'available' || state === 'active') {
    // Running = neutral for score
  } else if (state === 'stopped') {
    score -= 2;
    issues.push('Currently stopped');
  } else if (state === 'terminated' || state === 'deleted') {
    score -= 5;
    issues.push('Terminated/deleted');
  } else if (state === 'error' || state === 'failed') {
    score -= 4;
    issues.push('Error state');
  }

  // Waste detection
  const waste = getWasteInfo(resource, type);
  if (waste) {
    score -= 2;
    issues.push('Incurring cost while inactive');
  }

  // CPU utilization for running compute (if 0% = idle)
  if (type === 'Compute' && (state === 'running' || state === 'active')) {
    if (resource.cpu_utilization !== undefined && resource.cpu_utilization < 5) {
      score -= 2;
      issues.push('Very low CPU utilization');
    }
  }

  // Clamp score to 0-10
  score = Math.max(0, Math.min(10, score));

  // Determine color and emoji
  let color: string;
  let emoji: string;
  if (score >= 8) {
    color = 'emerald';
    emoji = '🟢';
  } else if (score >= 5) {
    color = 'amber';
    emoji = '🟡';
  } else {
    color = 'red';
    emoji = '🔴';
  }

  return { score, color, emoji, issues };
};

// -- Components --

// Stopped Duration Badge - Fetches from Audit API
const StoppedDurationBadge: React.FC<{ resourceId: string; compartmentId: string }> = ({ resourceId, compartmentId }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['lifecycle', resourceId],
    queryFn: () => cloudApi.getResourceLifecycle(resourceId, compartmentId),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1, // Only retry once
    enabled: !!resourceId && !!compartmentId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <i className="fas fa-spinner fa-spin"></i>
        <span>Checking...</span>
      </div>
    );
  }

  if (error || !data?.stopped_days) {
    return null; // Don't show if error or no data
  }

  const days = data.stopped_days;
  const urgency = days > 90 ? 'text-red-500' : days > 30 ? 'text-amber-500' : 'text-gray-500';

  return (
    <div className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
      <span className="text-gray-500 flex items-center gap-1">
        <i className="fas fa-clock text-gray-400"></i> Stopped Duration
      </span>
      <span className={`font-bold ${urgency}`}>
        {days} days
      </span>
    </div>
  );
};

// 2. Resource Card (Professional Single-Resource View)
const GlassResourceCard: React.FC<{ resource: any, type: string, compartmentId?: string }> = ({ resource, type, compartmentId }) => {
  const navigate = useNavigate();

  const getStatusBadge = (state: string) => {
    const s = state?.toLowerCase() || 'unknown';
    let styles = 'bg-gray-100 text-gray-800 border-gray-200';
    let icon = 'fa-question-circle';
    let dotColor = 'bg-gray-400';

    if (s === 'running' || s === 'available' || s === 'active') {
      styles = 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800';
      icon = 'fa-check-circle';
      dotColor = 'bg-emerald-500';
    } else if (s === 'stopped' || s === 'terminated' || s === 'inactive') {
      styles = 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700';
      icon = 'fa-stop-circle';
      dotColor = 'bg-gray-400';
    } else if (s === 'provisioning' || s === 'starting' || s === 'stopping' || s === 'creating' || s === 'updating') {
      styles = 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800';
      icon = 'fa-sync fa-spin';
      dotColor = 'bg-amber-500';
    } else if (s === 'failed' || s === 'error') {
      styles = 'bg-red-50 text-red-700 border-red-100 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800';
      icon = 'fa-exclamation-circle';
      dotColor = 'bg-red-500';
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${styles}`}>
        <span className={`w-1.5 h-1.5 rounded-full mr-2 ${dotColor}`}></span>
        {state}
      </span>
    );
  };

  const getIconForType = (t: string) => {
    switch (t) {
      case 'Database': return 'fa-database';
      case 'Cluster': return 'fa-cubes';
      case 'Load Balancer': return 'fa-network-wired';
      case 'Networking': return 'fa-project-diagram';
      case 'Network': return 'fa-project-diagram';
      case 'Volume': return 'fa-hdd';
      case 'Storage': return 'fa-hdd';
      case 'Gateway': return 'fa-door-open';
      case 'Bucket': return 'fa-bucket';
      case 'File System': return 'fa-folder-tree';
      case 'Vault': return 'fa-key';
      case 'Secret': return 'fa-lock';
      default: return 'fa-server';
    }
  };

  const typeColor =
    type === 'Database' ? 'green' :
      type === 'Cluster' ? 'indigo' :
        type === 'Load Balancer' ? 'yellow' :
          type === 'Networking' ? 'purple' :
            type === 'Network' ? 'purple' :
              type === 'Volume' ? 'orange' :
                type === 'Storage' ? 'orange' :
                  type === 'Bucket' ? 'cyan' :
                    type === 'Vault' ? 'red' :
                      type === 'Secret' ? 'rose' :
                        'blue';

  const healthScore = getHealthScore(resource, type);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 hover:shadow-lg transition-all duration-300 flex flex-col h-full group relative overflow-hidden">
      {/* Header */}
      <div className="p-5 flex justify-between items-start z-10">
        <div className="flex items-start flex-1 min-w-0">
          <div className={`mr-4 w-10 h-10 rounded-xl flex items-center justify-center bg-${typeColor}-50 text-${typeColor}-600 dark:bg-${typeColor}-900/20 dark:text-${typeColor}-400 shadow-sm`}>
            <i className={`fas ${getIconForType(type)} text-lg`}></i>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-gray-900 dark:text-white text-sm truncate max-w-[140px]" title={resource.display_name}>
              {resource.display_name}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide bg-gray-100 dark:bg-gray-700 text-gray-500`}>
                {type}
              </span>
            </div>
          </div>
        </div>
        {/* Health Score Badge */}
        <div
          className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-bold bg-${healthScore.color}-50 dark:bg-${healthScore.color}-900/30 text-${healthScore.color}-600 dark:text-${healthScore.color}-400`}
          title={healthScore.issues.length > 0 ? healthScore.issues.join(', ') : 'No issues detected'}
        >
          <span>{healthScore.emoji}</span>
          <span>{healthScore.score}/10</span>
        </div>
      </div>

      <div className="px-5 pb-2">
        {getStatusBadge(resource.lifecycle_state)}
      </div>

      {/* Body Statistics */}
      <div className="p-5 flex-grow space-y-4">
        {/* Key Metrics Grid */}
        <div className="space-y-2 text-xs">
          <div className="flex justify-between border-b border-gray-100 dark:border-gray-700 pb-2">
            <span className="text-gray-500">OCID</span>
            <span className="font-mono text-gray-400" title={resource.id}>{resource.id?.slice(-8)}...</span>
          </div>

          {type === 'Compute' ? (
            <>
              <div className="flex justify-between"><span className="text-gray-500">Shape</span><span className="font-medium">{resource.shape || 'N/A'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Domain</span><span className="font-medium">{resource.availability_domain?.slice(-3) || 'N/A'}</span></div>
            </>
          ) : type === 'Database' ? (
            <>
              <div className="flex justify-between"><span className="text-gray-500">Edition</span><span className="font-medium truncate max-w-[100px]" title={resource.database_edition}>{resource.database_edition?.replace('ENTERPRISE_EDITION', 'EE').replace('STANDARD_EDITION', 'SE') || 'N/A'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Cores</span><span className="font-medium">{resource.cpu_core_count || '-'}</span></div>
            </>
          ) : type === 'Cluster' ? (
            <div className="flex justify-between"><span className="text-gray-500">K8s Version</span><span className="font-medium">{resource.kubernetes_version || 'N/A'}</span></div>
          ) : (
            <div className="flex justify-between"><span className="text-gray-500">Subtype</span><span className="font-medium">{resource.resource_type || 'N/A'}</span></div>
          )}

          <div className="flex justify-between pt-2">
            <span className="text-gray-500">Created</span>
            <span className="font-medium">{resource.time_created ? new Date(resource.time_created).toLocaleDateString() : 'N/A'}</span>
          </div>
        </div>

        {/* Utilization (Fake/Real) if Running */}
        {(resource.cpu_utilization !== undefined || resource.lifecycle_state === 'RUNNING') && type === 'Compute' && (
          <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500 font-medium">CPU Utilization</span>
              <span className={`font-bold ${(resource.cpu_utilization || 0) > 80 ? 'text-red-500' : 'text-gray-700 dark:text-gray-300'}`}>
                {resource.cpu_utilization || 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${(resource.cpu_utilization || 0) > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                style={{ width: `${resource.cpu_utilization || 0}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Intelligence Layer - Cost & Status Insights */}
        <div className="space-y-2 mt-auto pt-3 border-t border-gray-100 dark:border-gray-700">
          {/* Estimated Cost */}
          {(() => {
            const cost = getEstimatedCost(resource, type);
            return cost > 0 ? (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500 flex items-center gap-1">
                  <i className="fas fa-coins text-amber-500"></i> Est. Cost
                </span>
                <span className="font-bold text-gray-700 dark:text-gray-300">
                  ${cost}/mo
                </span>
              </div>
            ) : null;
          })()}

          {/* Stopped Duration - Fetched from Audit API */}
          {['stopped', 'terminated', 'inactive'].includes(resource.lifecycle_state?.toLowerCase()) && compartmentId && (
            <StoppedDurationBadge resourceId={resource.id} compartmentId={compartmentId} />
          )}

          {/* Waste Alert */}
          {(() => {
            const waste = getWasteInfo(resource, type);
            return waste ? (
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-2 text-xs">
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                  <i className="fas fa-exclamation-triangle"></i>
                  <span className="font-medium">{waste.reason}</span>
                </div>
                {waste.amount > 0 && (
                  <div className="text-red-500 font-bold mt-1">
                    💸 Wasting ~${waste.amount}/mo
                  </div>
                )}
              </div>
            ) : null;
          })()}

          {/* Zombie Badge - Only for TERMINATED/DELETED resources */}
          {isZombieResource(resource) && (
            <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-2 text-xs">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <i className="fas fa-ghost"></i>
                <span className="font-medium">Cleanup Candidate</span>
              </div>
              <div className="text-amber-500 text-[10px] mt-1">
                Resource is terminated/deleted. Consider removing from tracking.
              </div>
            </div>
          )}
        </div>
      </div>

      <div className={`h-1 w-full bg-gradient-to-r from-${typeColor}-400 to-${typeColor}-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left`}></div>
    </div>
  );
};

// -- Main Page --
export function CloudResourcesPage() {
  const { data: compartments, isLoading: compartmentsLoading } = useCompartments();
  const [selectedCompartmentId, setSelectedCompartmentId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Auto-select first compartment
  useEffect(() => {
    if (compartments && compartments.length > 0 && (!selectedCompartmentId || selectedCompartmentId === 'test-compartment')) {
      setSelectedCompartmentId(compartments[0].id);
    }
  }, [compartments, selectedCompartmentId]);

  // Fetch Resources (Wait for valid compartment) - Fetching all types now
  const {
    data: resourceSummary,
    isLoading: resourcesLoading,
    error,
  } = useAllResources(
    selectedCompartmentId
  );

  // Process and Filter Data
  const { data, stats } = useMemo(() => {
    if (!resourceSummary?.resources) return {
      data: {
        'Compute': [],
        'Cluster': [],
        'Database': [],
        'Load Balancer': [],
        'Networking': [],
        'Storage': [],
        'Security': []
      },
      stats: null
    };

    const r = resourceSummary.resources;

    // Group resources based on taxonomy
    const grouped = {
      'Compute': [
        ...(r.compute_instances || []).map(x => ({ ...x, display_type: 'Compute' }))
      ],
      'Cluster': [
        ...(r.oke_clusters || []).map(x => ({ ...x, display_type: 'Cluster' }))
      ],
      'Database': [
        ...(r.databases || []).map(x => ({ ...x, display_type: 'Database' }))
      ],
      'Load Balancer': [
        ...(r.load_balancers || []).map(x => ({ ...x, display_type: 'Load Balancer' }))
      ],
      'Networking': [
        ...(r.network_resources || []).map(x => ({ ...x, display_type: 'Network' })),
        ...(r.api_gateways || []).map(x => ({ ...x, display_type: 'Gateway' }))
      ],
      'Storage': [
        ...(r.block_volumes || []).map(x => ({ ...x, display_type: 'Volume' })),
        ...(r.file_systems || []).map(x => ({ ...x, display_type: 'File System' })),
        ...(r.object_storage_buckets || []).map(x => ({ ...x, display_type: 'Bucket' }))
      ],
      'Security': [
        ...(r.vaults || []).map(x => ({ ...x, display_type: 'Vault' }))
      ]
    };

    let totalCount = 0;
    let runningCount = 0;

    // Filter and Flatten for Stats
    const allResources = [
      ...grouped['Compute'],
      ...grouped['Cluster'],
      ...grouped['Database'],
      ...grouped['Load Balancer'],
      ...grouped['Networking'],
      ...grouped['Storage'],
      ...grouped['Security']
    ];

    // Stats Calculation
    let zombieCount = 0;
    let totalEstCost = 0;
    let wasteAmount = 0;

    allResources.forEach(r => {
      totalCount++;
      const s = r.lifecycle_state?.toLowerCase();
      if (s === 'running' || s === 'available' || s === 'active') runningCount++;

      // Calculate zombie resources
      if (isZombieResource(r)) zombieCount++;

      // Calculate total estimated cost
      totalEstCost += getEstimatedCost(r, r.display_type);

      // Calculate waste
      const waste = getWasteInfo(r, r.display_type);
      if (waste) wasteAmount += waste.amount;
    });

    const activeCompute = grouped['Compute'].filter(r => r.lifecycle_state === 'RUNNING' && r.display_type === 'Compute');
    const cpuSum = activeCompute.reduce((sum, r) => sum + ((r as any).cpu_utilization || 0), 0);
    const avgCpu = activeCompute.length ? Math.round(cpuSum / activeCompute.length) : 0;

    return {
      data: grouped,
      stats: {
        total: totalCount,
        running: runningCount,
        stopped: totalCount - runningCount,
        avgCpu: avgCpu,
        avgMem: 0,
        alerts: activeCompute.filter(r => ((r as any).cpu_utilization || 0) > 90).length,
        // New actionable stats
        zombieCount,
        totalEstCost,
        wasteAmount
      }
    };
  }, [resourceSummary]);


  // Filter logic for display
  const getFilteredList = (list: any[]) => {
    if (!list) return [];
    return list.filter(r => {
      const matchesSearch = !searchQuery ||
        r.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.id?.toLowerCase().includes(searchQuery.toLowerCase());

      const s = r.lifecycle_state?.toLowerCase() || '';
      let matchesStatus = true;
      if (statusFilter === 'RUNNING') {
        matchesStatus = ['running', 'available', 'active'].includes(s);
      } else if (statusFilter === 'WASTE') {
        // Show resources with waste alerts
        matchesStatus = getWasteInfo(r, r.display_type) !== null;
      } else if (statusFilter === 'ZOMBIE') {
        // Show zombie resources (stopped >30 days)
        matchesStatus = isZombieResource(r);
      }

      return matchesSearch && matchesStatus;
    });
  };

  // Loading State
  if (compartmentsLoading || (resourcesLoading && !resourceSummary)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" message="Scanning Cloud Resources..." />
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="p-8 flex flex-col items-center justify-center text-center">
        <div className="bg-red-50 dark:bg-red-900/30 p-6 rounded-full mb-4">
          <i className="fas fa-exclamation-triangle text-4xl text-red-500"></i>
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Resource Scan Failed</h2>
        <p className="text-gray-500 mb-6 max-w-md">{error instanceof Error ? error.message : 'Unknown error occurred'}</p>
        <button onClick={() => window.location.reload()} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
          Retry Connection
        </button>
      </div>
    );
  }

  const computeList = getFilteredList(data['Compute']);
  const clusterList = getFilteredList(data['Cluster']);
  const dbList = getFilteredList(data['Database']);
  const lbList = getFilteredList(data['Load Balancer']);
  const netList = getFilteredList(data['Networking']);
  const storageList = getFilteredList(data['Storage']);
  const securityList = getFilteredList(data['Security']);

  return (
    <div className="space-y-8 pb-12 w-full max-w-full overflow-hidden animate-fade-in">

      {/* Hero */}
      <PremiumHero
        title="OCI Resource Observability"
        subtitle="Deep dive into your infrastructure inventory, status, and health metrics."
        pattern="default"
        colorCombo="purple" // Different color for distinction
        stats={[
          { label: 'Total Assets', value: (stats?.total || 0).toString() },
          { label: 'Active', value: (stats?.running || 0).toString() }
        ]}
      />

      {/* Controls: Compartment + Search */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="w-full md:w-1/3">
          <CompartmentSelector
            compartments={compartments || []}
            selectedCompartmentId={selectedCompartmentId}
            onCompartmentChange={setSelectedCompartmentId}
            loading={compartmentsLoading}
          />
        </div>

        <div className="flex gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            <input
              type="text"
              placeholder="Search by name or OCID..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all outline-none"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Smart Filters */}
          <div className="flex bg-gray-100 dark:bg-gray-700 p-1 rounded-lg flex-wrap gap-1">
            {[
              { id: 'ALL', label: 'All', icon: 'fa-layer-group' },
              { id: 'RUNNING', label: 'Active', icon: 'fa-play-circle' },
              { id: 'WASTE', label: `💸 Waste (${stats?.wasteAmount || 0})`, icon: null },
              { id: 'ZOMBIE', label: `🗑️ Cleanup (${stats?.zombieCount || 0})`, icon: null },
            ].map((filter) => (
              <button
                key={filter.id}
                onClick={() => setStatusFilter(filter.id)}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all whitespace-nowrap ${statusFilter === filter.id
                  ? 'bg-white dark:bg-gray-600 shadow-sm text-gray-900 dark:text-white'
                  : 'text-gray-500 hover:text-gray-900'
                  }`}
              >
                {filter.icon && <i className={`fas ${filter.icon} mr-1`}></i>}
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Smart Recommendations Panel */}
      {stats && (stats.wasteAmount > 0 || stats.zombieCount > 0 || stats.stopped > 0) && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-800 rounded-lg flex items-center justify-center">
              <i className="fas fa-lightbulb text-blue-600 dark:text-blue-400 text-lg"></i>
            </div>
            <div>
              <h3 className="font-bold text-gray-900 dark:text-white">Quick Wins Available</h3>
              <p className="text-sm text-gray-500">Actions to optimize your infrastructure</p>
            </div>
          </div>

          <div className="space-y-3">
            {stats.wasteAmount > 0 && (
              <div className="flex items-start gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-100 dark:border-gray-700">
                <span className="text-xl">💰</span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white">
                    Save ${stats.wasteAmount}/month
                  </div>
                  <div className="text-sm text-gray-500">
                    {stats.stopped} stopped resources with attached storage still incurring costs
                  </div>
                </div>
                <button
                  onClick={() => setStatusFilter('WASTE')}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition"
                >
                  Review →
                </button>
              </div>
            )}

            {stats.zombieCount > 0 && (
              <div className="flex items-start gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-100 dark:border-gray-700">
                <span className="text-xl">🗑️</span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white">
                    Clean up {stats.zombieCount} terminated resources
                  </div>
                  <div className="text-sm text-gray-500">
                    Terminated/deleted resources still tracked in your inventory
                  </div>
                </div>
                <button
                  onClick={() => setStatusFilter('ZOMBIE')}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-lg transition"
                >
                  Review →
                </button>
              </div>
            )}

            {stats.stopped > 0 && stats.wasteAmount === 0 && (
              <div className="flex items-start gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-100 dark:border-gray-700">
                <span className="text-xl">ℹ️</span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {stats.stopped} resources currently stopped
                  </div>
                  <div className="text-sm text-gray-500">
                    These may be scheduled shutdowns - verify if intentional
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actionable Stats Bar */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassStatCard
            title="Total Resources"
            value={stats.total}
            subValue={`${stats.running} active`}
            icon="fas fa-cubes"
            color="blue"
          />
          <GlassStatCard
            title="Est. Monthly Cost"
            value={`$${stats.totalEstCost.toLocaleString()}`}
            subValue="Based on shape pricing"
            icon="fas fa-coins"
            color="amber"
          />
          <GlassStatCard
            title="Cost Waste"
            value={stats.wasteAmount > 0 ? `$${stats.wasteAmount}/mo` : 'None'}
            subValue={stats.wasteAmount > 0 ? `${stats.stopped} stopped resources` : 'All costs justified'}
            icon="fas fa-exclamation-triangle"
            color={stats.wasteAmount > 0 ? "red" : "emerald"}
          />
          <GlassStatCard
            title="Zombie Resources"
            value={stats.zombieCount}
            subValue={stats.zombieCount > 0 ? 'Inactive >30 days' : 'No zombies found'}
            icon="fas fa-ghost"
            color={stats.zombieCount > 0 ? "amber" : "gray"}
          />
        </div>
      )}

      {/* Resource Sections - 6 Distinct Categories */}
      <div className="space-y-12">

        {/* 1. Compute Section */}
        {computeList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-lg">
                <i className="fas fa-server text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Compute Instances</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{computeList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {computeList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 2. Clusters Section */}
        {clusterList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 text-blue-600 rounded-lg">
                <i className="fas fa-cubes text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">OKE Clusters</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{clusterList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {clusterList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 3. Database Section */}
        {dbList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 text-green-600 rounded-lg">
                <i className="fas fa-database text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Databases</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{dbList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {dbList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 4. Load Balancer Section */}
        {lbList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 rounded-lg">
                <i className="fas fa-network-wired text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Load Balancers</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{lbList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {lbList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 5. Networking Section */}
        {netList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 text-purple-600 rounded-lg">
                <i className="fas fa-project-diagram text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Networking</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{netList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {netList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 6. Storage Section */}
        {storageList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-lg">
                <i className="fas fa-hdd text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Storage</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{storageList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {storageList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}

        {/* 7. Security Section (Vaults & Secrets) */}
        {securityList.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-red-100 dark:bg-red-900/30 text-red-600 rounded-lg">
                <i className="fas fa-key text-xl"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Security (Vaults & Secrets)</h3>
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{securityList.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {securityList.map((r: any) => <GlassResourceCard key={r.id} resource={r} type={r.display_type} compartmentId={selectedCompartmentId} />)}
            </div>
          </div>
        )}
      </div>

      {computeList.length === 0 && clusterList.length === 0 && dbList.length === 0 && lbList.length === 0 && netList.length === 0 && storageList.length === 0 && securityList.length === 0 && (
        <div className="text-center py-20 bg-gray-50 dark:bg-gray-800/50 rounded-3xl border-dashed border-2 border-gray-200 dark:border-gray-700">
          <div className="inline-block p-6 rounded-full bg-blue-50 text-blue-500 mb-4 animate-bounce-slow">
            <i className="fas fa-search text-3xl"></i>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">No resources found</h3>
          <p className="text-gray-500 max-w-sm mx-auto mt-2">
            We couldn't find any resources matching your filters in this compartment.
          </p>
        </div>
      )}
    </div>
  );
}