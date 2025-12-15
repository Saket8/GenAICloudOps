import React, { useState, useEffect, useMemo } from 'react';
import { useCompartments, useAllResources } from '../../services/cloudService';
import { costAnalyzerService, CostInsightsSummary, OptimizationRecommendation } from '../../services/costAnalyzerService';
import { AccessAnalyzerService, AccessSummaryResponse } from '../../services/accessAnalyzerService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { ResourceCard } from '../ui/ResourceCard';
import { MetricsChart } from '../ui/MetricsChart';
import { ChangeDeltaCard } from '../ui/ChangeDeltaCard';
import { useSystemMetrics } from '../../hooks/useWebSocket';
import { useQuery } from '@tanstack/react-query';
import { PremiumHero } from '../ui/PremiumHero';
import { GlassStatCard } from '../ui/GlassStatCard';

// New Widget: Strategic Insight (Cost/Security)
const StrategicCard: React.FC<{
  title: string;
  score: number;
  metricLabel: string;
  metricValue: string;
  secondaryLabel: string;
  secondaryValue: string;
  icon: string;
  color: string;
  actionLabel?: string;
  actionLink?: string;
}> = ({ title, score, metricLabel, metricValue, secondaryLabel, secondaryValue, icon, color, actionLabel, actionLink }) => (
  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col justify-between h-full relative overflow-hidden group hover:shadow-md transition-all">
    <div className={`absolute top-0 right-0 w-32 h-32 bg-${color}-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 group-hover:opacity-20 transition-opacity`}></div>

    <div className="flex justify-between items-start mb-4 relative z-10">
      <div>
        <h4 className="font-bold text-gray-800 dark:text-white flex items-center text-lg">
          <i className={`fas ${icon} mr-2 text-${color}-500`}></i> {title}
        </h4>
        <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">AI-Driven Analysis</p>
      </div>
      <div className={`px-2 py-1 rounded text-xs font-bold text-${color}-700 bg-${color}-50 dark:bg-${color}-900/20`}>
        Score: {score}
      </div>
    </div>

    <div className="space-y-4 mb-4 relative z-10">
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3">
        <div className="text-xs text-gray-500 mb-1">{metricLabel}</div>
        <div className="text-xl font-bold text-gray-900 dark:text-white">{metricValue}</div>
      </div>
      <div className="flex justify-between items-center text-sm">
        <span className="text-gray-500">{secondaryLabel}</span>
        <span className="font-medium">{secondaryValue}</span>
      </div>
    </div>

    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
      <div className={`h-full bg-${color}-500 rounded-full transition-all duration-1000`} style={{ width: `${score}%` }}></div>
    </div>

    {actionLabel && actionLink && (
      <a
        href={actionLink}
        className={`mt-4 w-full py-2 px-4 rounded-lg text-center text-sm font-medium transition-all
          bg-${color}-50 dark:bg-${color}-900/20 text-${color}-700 dark:text-${color}-300
          hover:bg-${color}-100 dark:hover:bg-${color}-900/40 border border-${color}-200 dark:border-${color}-800`}
      >
        <i className="fas fa-arrow-right mr-2"></i>{actionLabel}
      </a>
    )}
  </div>
);

export const DashboardPage: React.FC = () => {
  const [selectedCompartmentId, setSelectedCompartmentId] = useState(localStorage.getItem('selectedCompartment') || '');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Real-time hooks
  const { metrics } = useSystemMetrics();
  const {
    data: resources,
    isLoading: resourcesLoading,
    error: resourcesError
  } = useAllResources(selectedCompartmentId);

  // Compartments
  const { data: compartments, isLoading: compartmentsLoading } = useCompartments();

  // Auto-select compartment
  useEffect(() => {
    if (compartments && compartments.length > 0 && !selectedCompartmentId) {
      setSelectedCompartmentId(compartments[0].id);
    }
  }, [compartments, selectedCompartmentId]);

  // LIVE Cost Insights from API
  const { data: costInsights, isLoading: costLoading } = useQuery<CostInsightsSummary>({
    queryKey: ['costInsights'],
    queryFn: () => costAnalyzerService.getCostInsightsSummary('monthly'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // LIVE Security Insights from API
  const { data: securityInsights, isLoading: securityLoading } = useQuery<AccessSummaryResponse>({
    queryKey: ['securityInsights', selectedCompartmentId],
    queryFn: () => AccessAnalyzerService.getAccessSummary(selectedCompartmentId || 'default'),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: !!selectedCompartmentId,
  });

  // LIVE Top Optimization Recommendation
  const { data: topRecommendation } = useQuery({
    queryKey: ['topRecommendation'],
    queryFn: async () => {
      const result = await costAnalyzerService.getPriorityRecommendations(1);
      return result.recommendations[0] || null;
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  // Stats derivation & Resource Grouping
  const resourceGroups = React.useMemo(() => {
    if (!resources?.resources) return {
      compute: [],
      clusters: [],
      networking: [],
      loadBalancers: [],
      database: [],
      storage: [],
      stats: { total: 0, active: 0, errors: 0 }
    };

    const r = resources.resources;

    // Define Groups
    const compute = r.compute_instances || [];
    const clusters = r.oke_clusters || [];
    const loadBalancers = r.load_balancers || [];
    const networking = [
      ...(r.network_resources || []),
      ...(r.api_gateways || [])
    ];
    const database = r.databases || [];
    const storage = [
      ...(r.block_volumes || []),
      ...(r.file_systems || [])
    ];

    // Calculate Stats with OKE node detection
    const all = [...compute, ...clusters, ...networking, ...loadBalancers, ...database, ...storage];

    // Detect OKE worker nodes (names typically contain 'oke-' prefix)
    const okeNodes = compute.filter((c: any) =>
      c.display_name?.toLowerCase().includes('oke-') ||
      c.display_name?.toLowerCase().includes('node-')
    );
    const stoppedOkeNodes = okeNodes.filter((c: any) =>
      ['stopped', 'terminated'].includes(c.lifecycle_state?.toLowerCase() || '')
    );
    const stoppedNonOkeInstances = compute.filter((c: any) =>
      ['stopped', 'terminated'].includes(c.lifecycle_state?.toLowerCase() || '') &&
      !c.display_name?.toLowerCase().includes('oke-') &&
      !c.display_name?.toLowerCase().includes('node-')
    );

    return {
      compute,
      clusters,
      networking,
      loadBalancers,
      database,
      storage,
      stats: {
        total: all.length,
        active: all.filter(item =>
          ['running', 'available', 'active'].includes(item.lifecycle_state?.toLowerCase() || '')
        ).length,
        errors: all.filter(item =>
          ['stopped', 'terminated', 'failed', 'inactive'].includes(item.lifecycle_state?.toLowerCase() || '')
        ).length,
        // New: Breakdown for context
        stoppedOkeNodes: stoppedOkeNodes.length,
        stoppedOther: stoppedNonOkeInstances.length +
          all.filter(item =>
            !compute.includes(item) &&
            ['stopped', 'terminated', 'failed', 'inactive'].includes(item.lifecycle_state?.toLowerCase() || '')
          ).length
      }
    };
  }, [resources]);

  const { stats, compute, clusters, networking, loadBalancers, database, storage } = resourceGroups;

  const handleCompartmentChange = (id: string) => {
    setSelectedCompartmentId(id);
    localStorage.setItem('selectedCompartment', id);
  };

  // Helper to filter resources
  const getFilteredResources = (list: any[]) => {
    if (!list) return [];
    return list.filter(r => {
      const matchesSearch = !searchQuery ||
        r.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.id?.toLowerCase().includes(searchQuery.toLowerCase());

      const s = r.lifecycle_state?.toLowerCase() || '';
      let matchesStatus = true;
      if (statusFilter === 'RUNNING') matchesStatus = ['running', 'available', 'active'].includes(s);
      if (statusFilter === 'STOPPED') matchesStatus = ['stopped', 'terminated', 'inactive'].includes(s);

      return matchesSearch && matchesStatus;
    });
  };

  // COMPUTED: Overall health percentage based on actual resource states
  const computedHealthPct = useMemo(() => {
    if (stats.total === 0) return 100;
    return Math.round((stats.active / stats.total) * 100);
  }, [stats.active, stats.total]);

  // Determine health status message
  const healthStatusMessage = useMemo(() => {
    if (stats.total === 0) return 'No Resources';
    if (computedHealthPct >= 90) return 'Excellent';
    if (computedHealthPct >= 70) return 'Good';
    if (computedHealthPct >= 50) return 'Fair';
    return 'Needs Attention';
  }, [computedHealthPct, stats.total]);

  if (resourcesError) return (
    <div className="flex flex-col items-center justify-center h-96 text-center animate-fade-in">
      <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-full mb-6">
        <i className="fas fa-exclamation-triangle text-4xl text-red-500"></i>
      </div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Dashboard Error</h3>
      <p className="text-gray-500 max-w-md">{resourcesError instanceof Error ? resourcesError.message : 'Failed to load dashboard resources'}</p>
      <button onClick={() => window.location.reload()} className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
        Reload Dashboard
      </button>
    </div>
  );

  return (
    <div className="space-y-8 animate-fade-in pb-12">

      {/* Premium Header */}
      <PremiumHero
        title="Welcome back, System Administrator"
        subtitle="Here is your cloud operations overview for today."
        pattern="waves"
        colorCombo="blue"
        stats={[
          {
            label: 'System Status',
            value: stats.total === 0 ? 'Loading...' : computedHealthPct >= 70 ? 'Healthy' : 'Degraded'
          },
          {
            label: 'Critical Findings',
            value: (securityInsights?.risk_overview?.critical_findings_count ?? 0).toString()
          }
        ]}
      />

      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="w-full md:w-1/3">
          <CompartmentSelector
            compartments={compartments || []}
            selectedCompartmentId={selectedCompartmentId}
            onCompartmentChange={handleCompartmentChange}
            loading={compartmentsLoading}
          />
        </div>
        <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto items-center">
          <div className="relative w-full md:w-64">
            <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            <input
              type="text"
              placeholder="Search resources..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
            {['ALL', 'RUNNING', 'STOPPED'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${statusFilter === status
                  ? 'bg-white dark:bg-gray-600 shadow-sm text-gray-900 dark:text-white'
                  : 'text-gray-500 hover:text-gray-900'
                  }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <GlassStatCard
          title="Total Resources"
          value={stats.total}
          icon="fas fa-server"
          color="blue"
        />
        <GlassStatCard
          title="Running Services"
          value={stats.active}
          icon="fas fa-check-circle"
          color="emerald"
          subValue="Systems Operational"
        />
        <GlassStatCard
          title="Stopped / Inactive"
          value={stats.errors}
          icon="fas fa-stop-circle"
          color={(stats.stoppedOther ?? 0) > 0 ? "red" : "orange"}
          subValue={
            stats.errors === 0
              ? "All Systems Active"
              : (stats.stoppedOkeNodes ?? 0) > 0 && (stats.stoppedOther ?? 0) === 0
                ? `${stats.stoppedOkeNodes} OKE nodes (expected)`
                : (stats.stoppedOther ?? 0) > 0
                  ? `${stats.stoppedOther} need attention`
                  : "Review recommended"
          }
        />
        <GlassStatCard
          title="Overall Health"
          value={`${computedHealthPct}%`}
          icon="fas fa-heartbeat"
          color={computedHealthPct >= 70 ? "purple" : "orange"}
          subValue={healthStatusMessage}
        />
      </div>

      {/* Strategic Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StrategicCard
          title="Cost Efficiency"
          score={costInsights?.cost_health_score ?? 0}
          color="emerald"
          icon="fa-coins"
          metricLabel={topRecommendation ? "Top Optimization" : "Est. Monthly Savings"}
          metricValue={topRecommendation
            ? `Save $${topRecommendation.estimated_savings?.toFixed(0) || '0'}/mo`
            : costInsights ? costAnalyzerService.formatCurrency(costInsights.optimization_potential || 0) : '--'}
          secondaryLabel="Optimization Potential"
          secondaryValue={costInsights?.optimization_potential ? `$${costInsights.optimization_potential.toFixed(0)}` : 'Calculating...'}
          actionLabel="View Cost Analysis"
          actionLink="/cost-analysis"
        />
        <StrategicCard
          title="Security Posture"
          score={100 - (securityInsights?.risk_overview?.overall_risk_score ?? 0)}
          color="blue"
          icon="fa-shield-alt"
          metricLabel="Risk Level"
          metricValue={securityInsights?.risk_overview?.overall_risk_level || 'Analyzing...'}
          secondaryLabel="Critical Findings"
          secondaryValue={securityInsights?.risk_overview?.critical_findings_count?.toString() || '0'}
          actionLabel="Review Findings"
          actionLink="/alerts"
        />
      </div>

      {/* Main Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Resource Distribution"
          type="distribution"
          data={resources || undefined}
          loading={resourcesLoading}
        />
        <ChangeDeltaCard
          title="Operational Insights"
          stats={stats}
          topRecommendation={topRecommendation}
          criticalFindings={securityInsights?.risk_overview?.critical_findings_count}
          loading={resourcesLoading || costLoading || securityLoading}
        />
      </div>

      {/* Resource Lists - Only show cards for resources that exist in compartment */}
      {resources?.resources && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
          {compute.length > 0 && (
            <ResourceCard
              title="Compute Instances"
              icon="fas fa-server"
              resources={getFilteredResources(compute)}
              resourceType="compute"
              color="blue"
            />
          )}
          {clusters.length > 0 && (
            <ResourceCard
              title="OKE Clusters"
              icon="fas fa-cubes"
              resources={getFilteredResources(clusters)}
              resourceType="kubernetes"
              color="indigo"
            />
          )}
          {database.length > 0 && (
            <ResourceCard
              title="Databases"
              icon="fas fa-database"
              resources={getFilteredResources(database)}
              resourceType="database"
              color="green"
            />
          )}
          {loadBalancers.length > 0 && (
            <ResourceCard
              title="Load Balancers"
              icon="fas fa-network-wired"
              resources={getFilteredResources(loadBalancers)}
              resourceType="networking"
              color="yellow"
            />
          )}
          {networking.length > 0 && (
            <ResourceCard
              title="Networking"
              icon="fas fa-project-diagram"
              resources={getFilteredResources(networking)}
              resourceType="networking"
              color="purple"
            />
          )}
          {storage.length > 0 && (
            <ResourceCard
              title="Storage"
              icon="fas fa-hdd"
              resources={getFilteredResources(storage)}
              resourceType="storage"
              color="orange"
            />
          )}
        </div>
      )}
    </div>
  );
};