import React, { useState, useEffect } from 'react';
import { AccessAnalyzerService, RBACRole, RBACBinding, AccessSummaryResponse } from '../../services/accessAnalyzerService';

interface RBACNode {
  id: string;
  type: 'role' | 'subject';
  name: string;
  namespace?: string;
  kind?: string;
  x: number;
  y: number;
  connections: string[];
}

// RBAC Graph Visualization Component
const RBACGraphVisualization: React.FC<{ roles: RBACRole[]; bindings: RBACBinding[] }> = ({ roles, bindings }) => {
  const [nodes, setNodes] = useState<RBACNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    // Generate graph nodes from roles and bindings
    const generatedNodes: RBACNode[] = [];
    const nodePositions = new Map<string, { x: number; y: number }>();

    // Add role nodes
    roles.forEach((role, index) => {
      const nodeId = `role-${role.name}-${role.namespace || 'cluster'}`;
      const x = 100 + (index % 4) * 150;
      const y = 100 + Math.floor(index / 4) * 100;
      
      generatedNodes.push({
        id: nodeId,
        type: 'role',
        name: role.name,
        namespace: role.namespace,
        kind: role.kind,
        x,
        y,
        connections: []
      });
      nodePositions.set(nodeId, { x, y });
    });

    // Add subject nodes and connections
    bindings.forEach((binding, bindingIndex) => {
      const roleId = `role-${binding.role_ref.name}-${binding.namespace || 'cluster'}`;
      
      binding.subjects.forEach((subject, subjectIndex) => {
        const subjectId = `subject-${subject.kind}-${subject.name}-${subject.namespace || 'cluster'}`;
        
        // Check if subject node already exists
        let subjectNode = generatedNodes.find(n => n.id === subjectId);
        if (!subjectNode) {
          const x = 400 + (bindingIndex % 3) * 120;
          const y = 50 + subjectIndex * 80 + bindingIndex * 200;
          
          subjectNode = {
            id: subjectId,
            type: 'subject',
            name: subject.name,
            namespace: subject.namespace,
            kind: subject.kind,
            x,
            y,
            connections: [roleId]
          };
          generatedNodes.push(subjectNode);
        } else {
          subjectNode.connections.push(roleId);
        }

        // Add connection to role
        const roleNode = generatedNodes.find(n => n.id === roleId);
        if (roleNode && !roleNode.connections.includes(subjectId)) {
          roleNode.connections.push(subjectId);
        }
      });
    });

    setNodes(generatedNodes);
  }, [roles, bindings]);

  const getNodeColor = (node: RBACNode) => {
    if (node.type === 'role') {
      if (node.name.includes('admin') || node.name.includes('cluster-admin')) {
        return 'fill-red-500'; // High risk
      } else if (node.name.includes('edit') || node.name.includes('create')) {
        return 'fill-yellow-500'; // Medium risk
      }
      return 'fill-blue-500'; // Low risk
    }
    return 'fill-green-500'; // Subjects
  };

  const renderConnections = () => {
    const connections: JSX.Element[] = [];
    
    nodes.forEach(node => {
      node.connections.forEach(connectionId => {
        const targetNode = nodes.find(n => n.id === connectionId);
        if (targetNode) {
          connections.push(
            <line
              key={`${node.id}-${connectionId}`}
              x1={node.x + 30}
              y1={node.y + 15}
              x2={targetNode.x + 30}
              y2={targetNode.y + 15}
              stroke="#6B7280"
              strokeWidth="2"
              opacity="0.6"
            />
          );
        }
      });
    });
    
    return connections;
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-auto">
      <svg width="800" height="600" className="border border-gray-700 rounded">
        {/* Render connections first (behind nodes) */}
        {renderConnections()}
        
        {/* Render nodes */}
        {nodes.map(node => (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            className="cursor-pointer"
            onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
          >
            {/* Node circle */}
            <circle
              r="15"
              className={`${getNodeColor(node)} ${
                selectedNode === node.id ? 'stroke-white stroke-2' : 'stroke-gray-600'
              } hover:stroke-white transition-colors`}
              cx="15"
              cy="15"
            />
            
            {/* Node label */}
            <text
              x="35"
              y="20"
              className="fill-white text-xs font-medium"
              textAnchor="start"
            >
              {node.name.length > 15 ? `${node.name.substring(0, 12)}...` : node.name}
            </text>
            
            {/* Node type badge */}
            <text
              x="35"
              y="8"
              className="fill-gray-400 text-xs"
              textAnchor="start"
            >
              {node.kind || node.type}
            </text>
          </g>
        ))}
      </svg>
      
      {/* Legend */}
      <div className="mt-4 flex space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-gray-300">High Risk Roles</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <span className="text-gray-300">Medium Risk Roles</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <span className="text-gray-300">Low Risk Roles</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-gray-300">Subjects</span>
        </div>
      </div>
      
      {/* Selected node details */}
      {selectedNode && (
        <div className="mt-4 p-3 bg-gray-800 rounded border border-gray-600">
          <h4 className="text-white font-medium mb-2">Node Details</h4>
          {(() => {
            const node = nodes.find(n => n.id === selectedNode);
            return node ? (
              <div className="text-sm text-gray-300">
                <p><strong>Name:</strong> {node.name}</p>
                <p><strong>Type:</strong> {node.type}</p>
                {node.namespace && <p><strong>Namespace:</strong> {node.namespace}</p>}
                {node.kind && <p><strong>Kind:</strong> {node.kind}</p>}
                <p><strong>Connections:</strong> {node.connections.length}</p>
              </div>
            ) : null;
          })()}
        </div>
      )}
    </div>
  );
};

// Updated RBAC Analysis Tab with real data
const RBACAnalysisTab = () => {
  const [rbacData, setRbacData] = useState<{ roles: RBACRole[]; bindings: RBACBinding[] }>({ roles: [], bindings: [] });
  const [loading, setLoading] = useState(false);
  const [namespace, setNamespace] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [clusterName, setClusterName] = useState<string>('');

  const fetchRBACData = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching RBAC data for namespace:', namespace || 'all');
      const response = await AccessAnalyzerService.getRBACAnalysis(namespace || undefined);
      
      console.log('RBAC response:', response);
      setRbacData({ 
        roles: response.roles || [], 
        bindings: response.bindings || [] 
      });
      setClusterName(response.cluster_name || 'Unknown Cluster');
      
    } catch (error) {
      console.error('Failed to fetch RBAC data:', error);
      setError('Failed to fetch RBAC data from cluster. Please check your Kubernetes connection.');
      // Set empty data on error
      setRbacData({ roles: [], bindings: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRBACData();
  }, [namespace]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-white">Kubernetes RBAC Analysis</h3>
          {clusterName && (
            <p className="text-sm text-gray-400">Cluster: {clusterName}</p>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <i className="fas fa-search text-gray-400"></i>
            <input
              type="text"
              placeholder="Filter by namespace..."
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              className="bg-gray-700 text-white px-3 py-1 rounded text-sm border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <button
            onClick={fetchRBACData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            <i className={`fas fa-sync-alt ${loading ? 'fa-spin' : ''}`}></i>
            <span>Refresh</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">
            <i className="fas fa-download"></i>
            <span>Export</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900 bg-opacity-50 border border-red-500 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <i className="fas fa-exclamation-triangle text-red-400"></i>
            <span className="text-red-300">{error}</span>
          </div>
        </div>
      )}

      {/* RBAC Graph Visualization */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-white font-medium mb-4">RBAC Relationship Graph</h4>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <i className="fas fa-spinner fa-spin text-blue-500 text-2xl"></i>
            <span className="ml-2 text-gray-300">Loading RBAC data from cluster...</span>
          </div>
        ) : rbacData.roles.length === 0 && rbacData.bindings.length === 0 ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <i className="fas fa-exclamation-circle text-yellow-500 text-3xl mb-2"></i>
              <p className="text-gray-300">No RBAC data found</p>
              <p className="text-gray-500 text-sm">Check your Kubernetes cluster connection</p>
            </div>
          </div>
        ) : (
          <RBACGraphVisualization roles={rbacData.roles} bindings={rbacData.bindings} />
        )}
      </div>

      {/* RBAC Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-2">Total Roles</h4>
          <p className="text-2xl font-bold text-blue-400">{rbacData.roles.length}</p>
          <p className="text-gray-400 text-sm">Cluster + Namespaced</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-2">Role Bindings</h4>
          <p className="text-2xl font-bold text-green-400">{rbacData.bindings.length}</p>
          <p className="text-gray-400 text-sm">Active bindings</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-2">Subjects</h4>
          <p className="text-2xl font-bold text-yellow-400">
            {rbacData.bindings.reduce((total, binding) => total + binding.subjects.length, 0)}
          </p>
          <p className="text-gray-400 text-sm">Users + ServiceAccounts</p>
        </div>
      </div>
    </div>
  );
};

// Updated Summary Tab with real data
const SummaryTab = () => {
  const [summaryData, setSummaryData] = useState<AccessSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const fetchSummaryData = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching access summary...');
      const response = await AccessAnalyzerService.getAccessSummary('default');
      console.log('Summary response:', response);
      setSummaryData(response);
    } catch (error) {
      console.error('Failed to fetch summary data:', error);
      setError('Failed to fetch access control summary. Please check your connections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaryData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <i className="fas fa-spinner fa-spin text-blue-500 text-2xl"></i>
        <span className="ml-2 text-gray-300">Loading access control summary...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900 bg-opacity-50 border border-red-500 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <i className="fas fa-exclamation-triangle text-red-400"></i>
            <span className="text-red-300">{error}</span>
          </div>
          <button 
            onClick={fetchSummaryData}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!summaryData) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-400">
          <i className="fas fa-chart-bar text-4xl mb-4"></i>
          <p>No summary data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">Access Control Summary</h3>
        <button
          onClick={fetchSummaryData}
          className="flex items-center space-x-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          <i className="fas fa-sync-alt"></i>
          <span>Refresh</span>
        </button>
      </div>

      {/* Overall Risk Score */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-center">
          <h4 className="text-xl font-medium text-white mb-2">Overall Risk Score</h4>
          <div className={`text-4xl font-bold mb-2 ${
            summaryData.risk_overview.overall_risk_level === 'critical' ? 'text-red-400' :
            summaryData.risk_overview.overall_risk_level === 'high' ? 'text-orange-400' :
            summaryData.risk_overview.overall_risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {summaryData.risk_overview.overall_risk_score}/100
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            summaryData.risk_overview.overall_risk_level === 'critical' ? 'bg-red-900 text-red-300' :
            summaryData.risk_overview.overall_risk_level === 'high' ? 'bg-orange-900 text-orange-300' :
            summaryData.risk_overview.overall_risk_level === 'medium' ? 'bg-yellow-900 text-yellow-300' : 'bg-green-900 text-green-300'
          }`}>
            {(summaryData.risk_overview?.overall_risk_level ?? '').toString().toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* RBAC Summary */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4 flex items-center">
            <i className="fas fa-users mr-2 text-blue-400"></i>
            Kubernetes RBAC
          </h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-300">Total Roles</span>
              <span className="text-white font-medium">{summaryData.rbac_summary.total_roles}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Total Subjects</span>
              <span className="text-white font-medium">{summaryData.rbac_summary.total_subjects}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">High Risk Roles</span>
              <span className="text-red-400 font-medium">{summaryData.rbac_summary.high_risk_roles}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Medium Risk</span>
              <span className="text-yellow-400 font-medium">{summaryData.rbac_summary.medium_risk_roles}</span>
            </div>
          </div>
        </div>

        {/* IAM Summary */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4 flex items-center">
            <i className="fas fa-shield-alt mr-2 text-purple-400"></i>
            OCI IAM
          </h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-300">Total Policies</span>
              <span className="text-white font-medium">{summaryData.iam_summary.total_policies}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Compartments</span>
              <span className="text-white font-medium">{summaryData.iam_summary.compartments_analyzed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">High Risk Policies</span>
              <span className="text-red-400 font-medium">{summaryData.iam_summary.high_risk_policies}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Admin Users</span>
              <span className="text-yellow-400 font-medium">{summaryData.iam_summary.users_with_admin_access}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Findings */}
      {summaryData.critical_findings.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4 flex items-center">
            <i className="fas fa-exclamation-triangle mr-2 text-red-400"></i>
            Critical Findings
          </h4>
          <ul className="space-y-2">
            {summaryData.critical_findings.map((finding, index) => (
              <li key={index} className="flex items-start space-x-2">
                <i className="fas fa-circle text-red-400 text-xs mt-2"></i>
                <span className="text-gray-300">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-center text-gray-500 text-sm">
        Last updated: {new Date().toLocaleString()}
      </div>
    </div>
  );
};

interface TabItem {
  id: string;
  name: string;
  icon: string;
  component: React.ComponentType;
}

// Placeholder components for other tabs
const IAMPoliciesTab = () => (
  <div className="p-6">
    <h3 className="text-lg font-medium text-white mb-4">OCI IAM Policies</h3>
    <div className="bg-gray-800 rounded-lg p-4">
      <p className="text-gray-300">IAM policies table with risk scoring will be implemented next.</p>
    </div>
  </div>
);

const RecommendationsTab = () => (
  <div className="p-6">
    <h3 className="text-lg font-medium text-white mb-4">AI Recommendations</h3>
    <div className="bg-gray-800 rounded-lg p-4">
      <p className="text-gray-300">AI-powered security recommendations will be displayed here.</p>
    </div>
  </div>
);

const tabs: TabItem[] = [
  {
    id: 'summary',
    name: 'Summary',
    icon: 'fas fa-chart-bar',
    component: SummaryTab,
  },
  {
    id: 'rbac',
    name: 'RBAC Analysis',
    icon: 'fas fa-users',
    component: RBACAnalysisTab,
  },
  {
    id: 'iam',
    name: 'IAM Policies',
    icon: 'fas fa-file-alt',
    component: IAMPoliciesTab,
  },
  {
    id: 'recommendations',
    name: 'Recommendations',
    icon: 'fas fa-exclamation-triangle',
    component: RecommendationsTab,
  },
];

export function AccessAnalyzerPage() {
  const [activeTab, setActiveTab] = useState('summary');

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || SummaryTab;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-2">
          <i className="fas fa-shield-alt text-blue-400 text-3xl"></i>
          <h1 className="text-2xl font-bold text-white">Access Analyzer</h1>
        </div>
        <p className="text-blue-100">
          Unified analysis of Kubernetes RBAC and OCI IAM policies with AI-powered security recommendations.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800 rounded-lg">
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    isActive
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors duration-200 flex items-center space-x-2`}
                >
                  <i className={tab.icon}></i>
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[600px]">
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
} 