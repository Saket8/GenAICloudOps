import React, { useState, useEffect, useCallback } from 'react';
import { 
  costAnalyzerService, 
  CostAnalysisResponse, 
  TopCostlyResourcesResponse,
  CostInsightsSummary,
  PriorityRecommendations,
  CostHealthCheck,
  TopCostlyResource,
  OptimizationRecommendation,
  CostAnomaly
} from '../../services/costAnalyzerService';

// Cost Trend Chart Component
const CostTrendChart: React.FC<{ trends: any[] }> = ({ trends }) => {
  if (!trends?.length) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <i className="fas fa-chart-line text-4xl mb-2"></i>
          <p>No trend data available</p>
        </div>
      </div>
    );
  }

  const maxCost = Math.max(...trends.map(t => t.cost_amount));
  const minCost = Math.min(...trends.map(t => t.cost_amount));
  const range = maxCost - minCost || 1;

  return (
    <div className="h-64 relative">
      <svg className="w-full h-full" viewBox="0 0 800 200">
        {/* Grid lines */}
        {[0, 1, 2, 3, 4].map(i => (
          <line
            key={i}
            x1="60"
            y1={40 + i * 32}
            x2="760"
            y2={40 + i * 32}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}
        
        {/* Y-axis labels */}
        {[0, 1, 2, 3, 4].map(i => {
          const value = maxCost - (i * range / 4);
          return (
            <text
              key={i}
              x="50"
              y={45 + i * 32}
              fontSize="10"
              fill="#6b7280"
              textAnchor="end"
            >
              ${value.toFixed(0)}
            </text>
          );
        })}

        {/* Trend line */}
        <polyline
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          points={trends.map((trend, index) => {
            const x = 60 + (index * (700 / (trends.length - 1 || 1)));
            const y = 40 + ((maxCost - trend.cost_amount) / range) * 128;
            return `${x},${y}`;
          }).join(' ')}
        />

        {/* Data points */}
        {trends.map((trend, index) => {
          const x = 60 + (index * (700 / (trends.length - 1 || 1)));
          const y = 40 + ((maxCost - trend.cost_amount) / range) * 128;
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="4"
              fill="#3b82f6"
              className="hover:r-6 cursor-pointer"
            >
              <title>{`${trend.period}: $${trend.cost_amount.toFixed(2)}`}</title>
            </circle>
          );
        })}

        {/* X-axis labels */}
        {trends.map((trend, index) => {
          if (index % Math.max(1, Math.floor(trends.length / 6)) === 0) {
            const x = 60 + (index * (700 / (trends.length - 1 || 1)));
            return (
              <text
                key={index}
                x={x}
                y="185"
                fontSize="10"
                fill="#6b7280"
                textAnchor="middle"
              >
                {trend.period}
              </text>
            );
          }
          return null;
        })}
      </svg>
    </div>
  );
};

// Top Resources Table Component
const TopResourcesTable: React.FC<{ resources: TopCostlyResource[] }> = ({ resources }) => {
  const [sortField, setSortField] = useState<keyof TopCostlyResource>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const sortedResources = [...resources].sort((a, b) => {
    let aValue: any, bValue: any;
    
    if (sortField === 'rank') {
      aValue = a.rank;
      bValue = b.rank;
    } else {
      aValue = a.resource.cost_amount;
      bValue = b.resource.cost_amount;
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const handleSort = (field: keyof TopCostlyResource) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={() => handleSort('rank')}
            >
              Rank
              {sortField === 'rank' && (
                <i className={`ml-1 fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'}`}></i>
              )}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Resource
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Compartment
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={() => handleSort('resource' as any)}
            >
              Cost
              {sortField === 'resource' && (
                <i className={`ml-1 fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'}`}></i>
              )}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Cost Level
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Optimization Potential
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {sortedResources.map((item) => (
            <tr key={item.resource.resource_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                #{item.rank}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {item.resource.resource_name}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {item.resource.resource_id}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {item.resource.resource_type}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {item.resource.compartment_name}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                {costAnalyzerService.formatCurrency(item.resource.cost_amount, item.resource.currency)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${costAnalyzerService.getCostLevelColor(item.resource.cost_level)}`}>
                  {item.resource.cost_level}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {item.optimization_potential ? (
                  <span className="text-green-600 dark:text-green-400">
                    {costAnalyzerService.formatCurrency(item.optimization_potential)}
                  </span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Optimization Recommendations Panel
const RecommendationsPanel: React.FC<{ recommendations: OptimizationRecommendation[] }> = ({ recommendations }) => {
  const [expandedRec, setExpandedRec] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      {recommendations.map((rec) => (
        <div
          key={rec.recommendation_id}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          <div
            className="px-6 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
            onClick={() => setExpandedRec(expandedRec === rec.recommendation_id ? null : rec.recommendation_id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <i className={`${costAnalyzerService.getOptimizationTypeIcon(rec.optimization_type)} text-blue-500`}></i>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    {rec.resource_name}
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {rec.description}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm font-medium text-green-600 dark:text-green-400">
                    {costAnalyzerService.formatCurrency(rec.estimated_savings)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Potential savings
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    rec.priority >= 4 ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                    rec.priority >= 3 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                    'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  }`}>
                    Priority {rec.priority}
                  </span>
                  <i className={`fas fa-chevron-${expandedRec === rec.recommendation_id ? 'up' : 'down'} text-gray-400`}></i>
                </div>
              </div>
            </div>
          </div>

          {expandedRec === rec.recommendation_id && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Implementation Steps</h5>
                  <ol className="list-decimal list-inside space-y-1">
                    {rec.implementation_steps.map((step, index) => (
                      <li key={index} className="text-sm text-gray-600 dark:text-gray-300">
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
                <div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Effort Level</div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{rec.effort_level}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Risk Level</div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{rec.risk_level}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">AI Confidence</div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {costAnalyzerService.formatPercentage(rec.ai_confidence * 100)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Optimization Type</div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {(rec.optimization_type || '').toString().replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Cost Anomalies Component
const AnomaliesPanel: React.FC<{ anomalies: CostAnomaly[] }> = ({ anomalies }) => {
  return (
    <div className="space-y-4">
      {anomalies.map((anomaly) => (
        <div
          key={`${anomaly.resource_id}-${anomaly.detected_at}`}
          className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <div className={`w-3 h-3 rounded-full mt-1 ${costAnalyzerService.getAnomalySeverityColor(anomaly.severity)}`}></div>
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  {anomaly.resource_name}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                  {anomaly.description}
                </p>
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Current Cost:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {costAnalyzerService.formatCurrency(anomaly.current_cost)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Expected Cost:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {costAnalyzerService.formatCurrency(anomaly.expected_cost)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Deviation:</span>
                    <div className="font-medium text-red-600 dark:text-red-400">
                      +{anomaly.deviation_percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${costAnalyzerService.getCostLevelColor(anomaly.severity)}`}>
                {anomaly.severity}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Detected {new Date(anomaly.detected_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Main Cost Analyzer Page Component
export const CostAnalyzerPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'resources' | 'recommendations' | 'anomalies'>('overview');
  
  // Data states
  const [healthCheck, setHealthCheck] = useState<CostHealthCheck | null>(null);
  const [costAnalysis, setCostAnalysis] = useState<CostAnalysisResponse | null>(null);
  const [topResources, setTopResources] = useState<TopCostlyResourcesResponse | null>(null);
  const [insights, setInsights] = useState<CostInsightsSummary | null>(null);
  const [recommendations, setRecommendations] = useState<PriorityRecommendations | null>(null);

  // Filters
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [selectedCompartment, setSelectedCompartment] = useState<string>('all');
  const [resourceLimit, setResourceLimit] = useState(10);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔍 Starting cost data loading...');
      
      // Load health check first
      console.log('📋 Loading health check...');
      const healthData = await costAnalyzerService.getHealthCheck();
      setHealthCheck(healthData);
      console.log('✅ Health check loaded:', healthData);

      // Load each endpoint individually to isolate errors
      try {
        console.log('📊 Loading cost analysis...');
        const analysisData = await costAnalyzerService.analyzeCosts({
          period: selectedPeriod,
          include_forecasting: true,
          include_optimization: true,
          include_anomaly_detection: true
        });
        setCostAnalysis(analysisData);
        console.log('✅ Cost analysis loaded');
      } catch (err: any) {
        console.error('❌ Cost analysis failed:', err);
        throw new Error(`Cost analysis failed: ${err.response?.data?.detail || err.message}`);
      }

      try {
        console.log('📋 Loading top resources...');
        const topResourcesData = await costAnalyzerService.getTopCostlyResources({
          limit: resourceLimit,
          period: selectedPeriod,
          compartment_id: selectedCompartment === 'all' ? undefined : selectedCompartment
        });
        setTopResources(topResourcesData);
        console.log('✅ Top resources loaded');
      } catch (err: any) {
        console.error('❌ Top resources failed:', err);
        throw new Error(`Top resources failed: ${err.response?.data?.detail || err.message}`);
      }

      try {
        console.log('💡 Loading insights...');
        const insightsData = await costAnalyzerService.getCostInsightsSummary(selectedPeriod);
        setInsights(insightsData);
        console.log('✅ Insights loaded');
      } catch (err: any) {
        console.error('❌ Insights failed:', err);
        throw new Error(`Insights failed: ${err.response?.data?.detail || err.message}`);
      }

      try {
        console.log('🎯 Loading recommendations...');
        const recommendationsData = await costAnalyzerService.getPriorityRecommendations(5);
        setRecommendations(recommendationsData);
        console.log('✅ Recommendations loaded');
      } catch (err: any) {
        console.error('❌ Recommendations failed:', err);
        throw new Error(`Recommendations failed: ${err.response?.data?.detail || err.message}`);
      }

      console.log('🎉 All cost data loaded successfully!');

    } catch (err: any) {
      console.error('Failed to load cost data:', err);
      console.log('Error details:', err.response?.data);
      setError(err.response?.data?.detail || err.message || 'Failed to load cost analysis data');
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod, selectedCompartment, resourceLimit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Export functionality
  const handleExport = (format: 'pdf' | 'csv') => {
    if (!costAnalysis) return;
    
    const exportData = costAnalyzerService.prepareCostDataForExport(costAnalysis);
    
    if (format === 'csv') {
      // Simple CSV export for now
      const csvContent = [
        ['Resource Name', 'Type', 'Compartment', 'Cost', 'Cost Level'],
        ...exportData.resources.map((resource: any) => [
          resource.resource_name,
          resource.resource_type,
          resource.compartment_name,
          resource.cost_amount,
          resource.cost_level
        ])
      ].map(row => row.join(',')).join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cost-analysis-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // PDF export would require a PDF library - placeholder for now
      alert('PDF export functionality will be implemented with a PDF generation library');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading cost analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 dark:bg-red-900 border border-red-400 text-red-700 dark:text-red-200 px-4 py-3 rounded">
            <p className="font-bold">Error Loading Cost Data</p>
            <p>{error}</p>
            <button
              onClick={loadData}
              className="mt-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Cost Analyzer & Optimization
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Analyze costs, track trends, and discover optimization opportunities
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-3">
          <button
            onClick={() => handleExport('csv')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <i className="fas fa-download mr-2"></i>
            Export CSV
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <i className="fas fa-file-pdf mr-2"></i>
            Export PDF
          </button>
        </div>
      </div>

      {/* Health Status */}
      {healthCheck && (
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                healthCheck.status === 'healthy' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
              }`}>
                <i className={`fas fa-${healthCheck.status === 'healthy' ? 'check' : 'exclamation-triangle'}`}></i>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Cost Analyzer Status: {healthCheck.status}
                </h3>
                <div className="mt-1 flex space-x-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>OCI Billing: {healthCheck.oci_billing_available ? '✓' : '✗'}</span>
                  <span>AI Service: {healthCheck.ai_service_available ? '✓' : '✗ (Corporate Policy)'}</span>
                  <span>Data Fresh: {healthCheck.cost_data_fresh ? '✓' : '✗'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Period</label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Compartment</label>
              <select
                value={selectedCompartment}
                onChange={(e) => setSelectedCompartment(e.target.value)}
                className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="all">All Compartments</option>
                <option value="production">Production</option>
                <option value="development">Development</option>
                <option value="testing">Testing</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Resource Limit</label>
              <select
                value={resourceLimit}
                onChange={(e) => setResourceLimit(Number(e.target.value))}
                className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
                <option value={50}>Top 50</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      {insights && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <i className="fas fa-dollar-sign text-2xl text-blue-600"></i>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Cost</dt>
                    <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                      {costAnalyzerService.formatCurrency(insights.total_cost, insights.currency)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <i className="fas fa-chart-line text-2xl text-green-600"></i>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Optimization Potential</dt>
                    <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                      {costAnalyzerService.formatCurrency(insights.optimization_potential)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <i className="fas fa-exclamation-triangle text-2xl text-yellow-600"></i>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Anomalies</dt>
                    <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                      {insights.anomaly_count}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <i className="fas fa-heartbeat text-2xl text-purple-600"></i>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Health Score</dt>
                    <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                      {insights.cost_health_score}/100
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: 'fas fa-chart-pie' },
            { id: 'resources', name: 'Top Resources', icon: 'fas fa-list' },
            { id: 'recommendations', name: 'Recommendations', icon: 'fas fa-lightbulb' },
            { id: 'anomalies', name: 'Anomalies', icon: 'fas fa-exclamation-triangle' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <i className={`${tab.icon} mr-2`}></i>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && costAnalysis && Array.isArray(costAnalysis.cost_trends) && (
          <>
            {/* Cost Trends Chart */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Cost Trends ({selectedPeriod})
                </h3>
                <CostTrendChart trends={costAnalysis.cost_trends} />
              </div>
            </div>

            {/* Compartment Breakdown */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Cost by Compartment
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Array.isArray(costAnalysis.compartment_breakdown) && costAnalysis.compartment_breakdown.map((comp) => (
                    <div key={comp.compartment_id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{comp.compartment_name}</h4>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {comp.resource_count} resources
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {costAnalyzerService.formatCurrency(comp.total_cost)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {comp.cost_percentage.toFixed(1)}% of total
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'resources' && topResources && (
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Top {resourceLimit} Costly Resources
              </h3>
              <TopResourcesTable resources={topResources.resources} />
            </div>
          </div>
        )}

        {activeTab === 'recommendations' && recommendations && (
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Optimization Recommendations
                </h3>
                <div className="text-sm text-green-600 dark:text-green-400">
                  Total Potential Savings: {costAnalyzerService.formatCurrency(recommendations.total_potential_savings)}
                </div>
              </div>
              <RecommendationsPanel recommendations={recommendations.recommendations} />
            </div>
          </div>
        )}

        {activeTab === 'anomalies' && costAnalysis && Array.isArray(costAnalysis.anomalies) && (
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Cost Anomalies ({costAnalysis.anomalies.length} detected)
              </h3>
              <AnomaliesPanel anomalies={costAnalysis.anomalies} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 