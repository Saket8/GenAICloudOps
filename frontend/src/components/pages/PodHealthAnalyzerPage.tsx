import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { kubernetesService, Pod, PodStatusSummary, Namespace, PodLogs } from '../../services/kubernetesService';
import { mockKubernetesService } from '../../services/mockKubernetesService';
import { genaiService } from '../../services/genaiService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { EmptyState } from '../ui/EmptyState';

// Toggle between real and mock data for testing
const USE_MOCK_DATA = true; // Set to false to use real Kubernetes data

// Status badge component
const StatusBadge: React.FC<{ status: string; restartCount: number }> = ({ status, restartCount }) => {
  const getStatusColor = (status: string, restartCount: number) => {
    if (restartCount > 10) return 'bg-red-500';
    if (status === 'Running') return 'bg-green-500';
    if (status === 'Pending') return 'bg-yellow-500';
    if (status === 'Failed' || status === 'CrashLoopBackOff') return 'bg-red-500';
    if (status === 'Succeeded') return 'bg-blue-500';
    return 'bg-gray-500';
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getStatusColor(status, restartCount)}`}
    >
      {status}
      {restartCount > 0 && (
        <span className="ml-1 px-1 bg-white bg-opacity-30 rounded">
          {restartCount}↻
        </span>
      )}
    </span>
  );
};

// Pod log viewer component
const PodLogViewer: React.FC<{ 
  namespace: string; 
  podName: string; 
  isOpen: boolean; 
  onClose: () => void;
  k8sService: any; // Pass the service as a prop
}> = ({ namespace, podName, isOpen, onClose, k8sService }) => {
  const [logLines, setLogLines] = useState(100);
  const [selectedContainer, setSelectedContainer] = useState<string | undefined>();

  const { data: logs, isLoading: logsLoading, error: logsError } = useQuery({
    queryKey: ['pod-logs', namespace, podName, selectedContainer, logLines],
    queryFn: () => k8sService.getPodLogs(namespace, podName, {
      container: selectedContainer,
      lines: logLines
    }),
    enabled: isOpen,
    // ❌ REMOVED: EXTREMELY aggressive 5-second polling causing severe performance issues
  });

  const { data: aiAnalysis, isLoading: aiLoading } = useQuery({
    queryKey: ['pod-log-analysis', namespace, podName, logs?.logs],
    queryFn: async () => {
      if (!logs?.logs) return null;
      return await genaiService.troubleshootIssue({
        context: `Pod ${namespace}/${podName} logs analysis`,
        logs: logs.logs,
        pod_name: podName,
        namespace: namespace
      });
    },
    enabled: !!logs?.logs
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-11/12 h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Pod Logs: {namespace}/{podName}
          </h3>
          <div className="flex items-center space-x-4">
            <select
              value={logLines}
              onChange={(e) => setLogLines(Number(e.target.value))}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value={50}>50 lines</option>
              <option value={100}>100 lines</option>
              <option value={200}>200 lines</option>
              <option value={500}>500 lines</option>
            </select>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Logs Panel */}
          <div className="flex-1 flex flex-col">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Raw Logs</h4>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {logsLoading ? (
                <LoadingSpinner />
              ) : logsError ? (
                <div className="text-red-500">Error loading logs: {logsError.message}</div>
              ) : (
                <pre className="text-xs font-mono bg-black text-green-400 p-4 rounded overflow-auto whitespace-pre-wrap">
                  {logs?.logs || 'No logs available'}
                </pre>
              )}
            </div>
          </div>

          {/* AI Analysis Panel */}
          <div className="w-1/3 border-l border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                AI Analysis
                {aiLoading && <LoadingSpinner size="sm" className="inline ml-2" />}
              </h4>
            </div>
            <div className="p-4 overflow-auto">
              {aiAnalysis ? (
                <div className="space-y-4">
                  <div>
                    <h5 className="font-medium text-gray-900 dark:text-white mb-2">AI Analysis</h5>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {(aiAnalysis as any)?.content || (aiAnalysis as any)?.response || 'Analysis completed'}
                    </p>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-900 dark:text-white mb-2">Suggestions</h5>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      AI-powered analysis and troubleshooting suggestions available
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-sm">
                  AI analysis will appear here when logs are available
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Pod Health Analyzer Page
export function PodHealthAnalyzerPage() {
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(null);
  const [selectedPod, setSelectedPod] = useState<{ namespace: string; name: string } | null>(null);
  const [showOnlyProblems, setShowOnlyProblems] = useState(false);
  const queryClient = useQueryClient();

  // Select the appropriate service based on USE_MOCK_DATA flag
  const k8sService = USE_MOCK_DATA ? mockKubernetesService : kubernetesService;

  // Fetch namespaces
  const { data: namespaces } = useQuery({
    queryKey: ['namespaces'],
    queryFn: k8sService.getNamespaces,
    staleTime: 30000
  });

  // Fetch pod status summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['pod-status-summary', selectedNamespace],
    queryFn: () => k8sService.getPodStatusSummary(selectedNamespace || undefined),
    // ❌ REMOVED: Aggressive 30-second polling causing performance issues
  });

  // Fetch detailed pods
  const { data: pods, isLoading: podsLoading } = useQuery({
    queryKey: ['pods', selectedNamespace],
    queryFn: () => k8sService.getPods(selectedNamespace || undefined),
    // ❌ REMOVED: Aggressive 30-second polling causing performance issues
  });

  // Restart pod mutation
  const restartPodMutation = useMutation({
    mutationFn: ({ namespace, podName }: { namespace: string; podName: string }) =>
      k8sService.restartPod(namespace, podName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pods'] });
      queryClient.invalidateQueries({ queryKey: ['pod-status-summary'] });
    }
  });

  // Filter pods based on user preferences
  const filteredPods = pods?.filter(pod => {
    if (!showOnlyProblems) return true;
    return pod.status !== 'Running' || pod.restart_count > 5;
  }) || [];

  const handleRestartPod = (namespace: string, podName: string) => {
    if (confirm(`Are you sure you want to restart pod ${namespace}/${podName}?`)) {
      restartPodMutation.mutate({ namespace, podName });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Pod Health & Log Analyzer
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Monitor and analyze Kubernetes pod health, status, and logs with AI insights
              {USE_MOCK_DATA && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  Demo Mode
                </span>
              )}
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-4">
            <select
              value={selectedNamespace || ''}
              onChange={(e) => setSelectedNamespace(e.target.value || null)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Namespaces</option>
              {namespaces?.map(ns => (
                <option key={ns.name} value={ns.name}>{ns.name}</option>
              ))}
            </select>
            <label className="flex items-center text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={showOnlyProblems}
                onChange={(e) => setShowOnlyProblems(e.target.checked)}
                className="mr-2"
              />
              Show problems only
            </label>
          </div>
        </div>
      </div>

      {/* Status Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <i className="fas fa-cubes text-blue-600 dark:text-blue-400"></i>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Pods</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{summary.total_pods}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <i className="fas fa-heart text-green-600 dark:text-green-400"></i>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Healthy</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{summary.healthy_percentage}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                <i className="fas fa-refresh text-yellow-600 dark:text-yellow-400"></i>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Restarts</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{summary.total_restarts}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <i className="fas fa-exclamation-triangle text-red-600 dark:text-red-400"></i>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Problem Pods</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{summary.problem_pods.length}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pod Table */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Pod Status</h3>
        </div>
        
        {podsLoading ? (
          <div className="p-8 text-center">
            <LoadingSpinner />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading pods...</p>
          </div>
        ) : filteredPods.length === 0 ? (
          <EmptyState
            icon="fas fa-cubes"
            title="No pods found"
            description={showOnlyProblems ? "No problematic pods found. Great!" : "No pods are running in the selected namespace."}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Pod Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Namespace
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Restarts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Node
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Age
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredPods.map((pod) => (
                  <tr key={`${pod.namespace}-${pod.name}`} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {pod.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {pod.namespace}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={pod.status} restartCount={pod.restart_count} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {pod.restart_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {pod.node_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(pod.created_time).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => setSelectedPod({ namespace: pod.namespace, name: pod.name })}
                        className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        title="View logs"
                      >
                        <i className="fas fa-file-alt"></i>
                      </button>
                      <button
                        onClick={() => handleRestartPod(pod.namespace, pod.name)}
                        className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                        title="Restart pod"
                        disabled={restartPodMutation.isPending}
                      >
                        <i className="fas fa-redo"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pod Log Viewer Modal */}
      {selectedPod && (
        <PodLogViewer
          namespace={selectedPod.namespace}
          podName={selectedPod.name}
          isOpen={!!selectedPod}
          onClose={() => setSelectedPod(null)}
          k8sService={k8sService}
        />
      )}
    </div>
  );
} 