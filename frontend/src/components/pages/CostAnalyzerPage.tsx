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
  CostAnomaly,
  CostAnalysisRequest
} from '../../services/costAnalyzerService';
import { cloudService } from '../../services/cloudService';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import { LoadingSpinner } from '../ui/LoadingSpinner';

// -- Enhanced UI Components --

const FinOpsHero: React.FC<{ totalCost: number, currency: string, healthScore: number, period: string }> = ({ totalCost, currency, healthScore, period }) => {
  // Generate period label based on selected filter
  const getPeriodLabel = () => {
    const now = new Date();
    const monthName = now.toLocaleString('default', { month: 'long' });
    const year = now.getFullYear();
    const day = now.getDate();

    switch (period) {
      case 'mtd':
        return `${monthName} 1-${day}, ${year}`;
      case 'last_30_days':
        return 'Last 30 Days';
      case 'last_90_days':
        return 'Last 90 Days';
      case 'last_month':
        const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        return lastMonth.toLocaleString('default', { month: 'long', year: 'numeric' });
      case 'daily':
        return `Today (${monthName} ${day})`;
      case 'yearly':
        return 'Last 12 Months';
      default:
        return `${monthName} ${year}`;
    }
  };

  return (
    <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-cyan-900 rounded-3xl p-8 shadow-2xl mb-8 text-white relative overflow-hidden">
      {/* Abstract Shapes */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500 rounded-full mix-blend-overlay filter blur-3xl opacity-20 -mr-20 -mt-20"></div>
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-cyan-500 rounded-full mix-blend-overlay filter blur-3xl opacity-20 -ml-10 -mb-10"></div>

      <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
        <div>
          <div className="flex items-center space-x-2 mb-2 text-emerald-300">
            <i className="fas fa-search-dollar text-xl"></i>
            <span className="font-bold tracking-widest uppercase text-sm">OCI Cost Analysis</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-emerald-200">
            {costAnalyzerService.formatCurrency(totalCost, currency)}
          </h1>
          <p className="text-emerald-100 mt-2 flex items-center gap-2">
            <i className="fas fa-calendar-alt text-emerald-400"></i>
            <span className="font-semibold">{getPeriodLabel()}</span>
            <span className="text-emerald-200/60">•</span>
            <span className="text-emerald-200/80 text-sm">Actual costs from OCI Usage API</span>
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 flex flex-col items-center min-w-[140px]">
          <div className="text-xs text-emerald-200 uppercase font-bold mb-1">Cost Health</div>
          <div className="text-3xl font-bold">{healthScore}/100</div>
          <div className="w-full h-1.5 bg-black/20 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${healthScore}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

const GlassStatCard: React.FC<{
  title: string;
  value: string | number;
  subValue?: string;
  icon: string;
  color: string;
  trend?: 'up' | 'down' | 'neutral';
}> = ({ title, value, subValue, icon, color, trend }) => {
  const colorStyles = {
    emerald: 'from-emerald-500 to-emerald-600',
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
    red: 'from-red-500 to-red-600',
  }[color] || 'from-gray-500 to-gray-600';

  const iconColor = {
    emerald: 'text-emerald-500',
    blue: 'text-blue-500',
    purple: 'text-purple-500',
    orange: 'text-orange-500',
    red: 'text-red-500',
  }[color] || 'text-gray-500';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all group">
      <div className="flex justify-between items-start">
        <div>
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{title}</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white group-hover:scale-105 transition-transform origin-left">{value}</div>
          {subValue && <div className="text-xs font-medium text-gray-500 mt-1">{subValue}</div>}
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorStyles} flex items-center justify-center text-white shadow-lg`}>
          <i className={`${icon} text-lg`}></i>
        </div>
      </div>
    </div>
  );
};

// -- Redesigned Chart Component (Recharts) --
const CostTrendChart: React.FC<{ trends: any[] }> = ({ trends }) => {
  if (!trends?.length) {
    return (
      <div className="h-80 flex flex-col items-center justify-center text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-2xl">
        <i className="fas fa-chart-area text-4xl mb-4 opacity-50"></i>
        <p>No trend data available for this period</p>
      </div>
    );
  }

  return (
    <div className="h-80 w-full bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-sm font-bold text-gray-500 uppercase mb-6 ml-2">Spending Trend</h3>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" opacity={0.5} />
          <XAxis dataKey="period" stroke="#9CA3AF" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} />
          <Tooltip
            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
            itemStyle={{ color: '#065F46', fontWeight: 600 }}
          />
          <Area
            type="monotone"
            dataKey="cost_amount"
            stroke="#10B981"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorCost)"
            name="Cost"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Generic Donut Chart for Breakdowns
const DonutChart: React.FC<{ data: { name: string; value: number; color?: string }[] }> = ({ data }) => {
  if (!data || data.length === 0) return <div className="h-64 flex items-center justify-center text-gray-400">No data available</div>;

  // Add colors if missing, ensuring valid hex
  const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#14B8A6'];
  const chartData = data.map((item, index) => ({
    ...item,
    color: item.color || COLORS[index % COLORS.length]
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => `$${value.toFixed(2)}`}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
          />
          <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ fontSize: '12px' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

// -- Redesigned Table Component --
const TopResourcesTable: React.FC<{ resources: TopCostlyResource[] }> = ({ resources }) => {
  return (
    <div className="overflow-hidden bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              {['Rank', 'Resource Name', 'Type', 'Cost (USD)', 'Status', 'Savings Potential'].map((header) => (
                <th key={header} className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {resources.map((item) => (
              <tr key={item.resource.resource_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 text-xs font-bold text-gray-600 dark:text-gray-300">
                    #{item.rank}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-bold text-gray-900 dark:text-white">{item.resource.resource_name}</div>
                  <div className="text-xs text-gray-400 font-mono mt-1 truncate max-w-[150px]">{item.resource.resource_id}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                    {item.resource.resource_type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 dark:text-white">
                  {costAnalyzerService.formatCurrency(item.resource.cost_amount, item.resource.currency)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${costAnalyzerService.getCostLevelColor(item.resource.cost_level)}`}>
                    {item.resource.cost_level}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  {item.optimization_potential ? (
                    <span className="flex items-center">
                      <i className="fas fa-arrow-down mr-1 text-xs"></i>
                      {costAnalyzerService.formatCurrency(item.optimization_potential)}
                    </span>
                  ) : <span className="text-gray-300">-</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// -- Redesigned Recommendations Component --
const RecommendationsPanel: React.FC<{ recommendations: OptimizationRecommendation[] }> = ({ recommendations }) => {
  const [expandedRec, setExpandedRec] = useState<string | null>(null);

  if (!recommendations?.length) return <div>No recommendations available.</div>;

  return (
    <div className="grid grid-cols-1 gap-4">
      {recommendations.map((rec) => (
        <div
          key={rec.recommendation_id}
          className={`
                bg-white dark:bg-gray-800 rounded-2xl border transition-all duration-300 overflow-hidden
                ${expandedRec === rec.recommendation_id
              ? 'border-blue-500 shadow-md ring-1 ring-blue-500'
              : 'border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md hover:border-blue-300'}
            `}
        >
          <div
            className="p-5 cursor-pointer"
            onClick={() => setExpandedRec(expandedRec === rec.recommendation_id ? null : rec.recommendation_id)}
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400`}>
                  <i className={costAnalyzerService.getOptimizationTypeIcon(rec.optimization_type)}></i>
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 dark:text-white text-base">{rec.resource_name}</h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{rec.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right hidden sm:block">
                  <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{costAnalyzerService.formatCurrency(rec.estimated_savings)}</div>
                  <div className="text-xs text-gray-400 uppercase">Savings</div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${rec.priority >= 4 ? 'bg-red-100 text-red-700' :
                  rec.priority >= 3 ? 'bg-orange-100 text-orange-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                  Priority {rec.priority}
                </div>
              </div>
            </div>
          </div>

          {/* Expanded Details */}
          {expandedRec === rec.recommendation_id && (
            <div className="bg-gray-50 dark:bg-gray-900/50 p-6 border-t border-gray-100 dark:border-gray-700 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2">
                  <h5 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Action Plan</h5>
                  <ol className="space-y-2">
                    {rec.implementation_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start text-sm text-gray-700 dark:text-gray-300">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white border border-gray-300 flex items-center justify-center text-xs font-bold mr-2 text-gray-500">{idx + 1}</span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <h5 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Analysis</h5>
                  <div className="space-y-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Effort</span>
                      <span className="font-medium">{rec.effort_level}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Risk</span>
                      <span className="font-medium">{rec.risk_level}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">AI Confidence</span>
                      <span className="font-bold text-blue-600">{costAnalyzerService.formatPercentage(rec.ai_confidence * 100)}</span>
                    </div>
                  </div>
                  <button className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold py-2 rounded-lg transition-colors">
                    Apply Fix
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Cost Anomalies Component (Modernized)
const AnomaliesPanel: React.FC<{ anomalies: CostAnomaly[] }> = ({ anomalies }) => {
  if (!anomalies?.length) return <div className="text-center py-8 text-gray-500">No anomalies detected in this period.</div>;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {anomalies.map((anomaly, idx) => (
        <div key={idx} className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
          <div className={`absolute top-0 left-0 w-1 h-full ${costAnalyzerService.getAnomalySeverityColor(anomaly.severity).replace('text-', 'bg-')}`}></div>
          <div className="flex justify-between items-start mb-4 pl-3">
            <div className="flex items-center gap-2">
              <i className="fas fa-bolt text-amber-500 text-xl"></i>
              <h4 className="font-bold text-gray-900 dark:text-white truncate max-w-[150px]">{anomaly.resource_name}</h4>
            </div>
            <span className={`text-xs font-bold uppercase px-2 py-1 rounded bg-gray-100 ${costAnalyzerService.getAnomalySeverityColor(anomaly.severity)}`}>
              {anomaly.severity}
            </span>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 pl-3 min-h-[40px]">{anomaly.description}</p>

          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 pl-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-xs text-gray-400">Actual</div>
                <div className="font-bold text-gray-900 dark:text-white">{costAnalyzerService.formatCurrency(anomaly.current_cost)}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400">Expected</div>
                <div className="font-medium text-gray-600 dark:text-gray-400">{costAnalyzerService.formatCurrency(anomaly.expected_cost)}</div>
              </div>
            </div>
            <div className="mt-2 text-xs font-bold text-red-500 text-center bg-red-50 dark:bg-red-900/10 py-1 rounded">
              +{anomaly.deviation_percentage}% Deviation
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// -- Main Page Component --
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
  const [selectedPeriod, setSelectedPeriod] = useState('mtd'); // Default: Month-to-Date
  const [selectedCompartment, setSelectedCompartment] = useState<string>('all');
  const [selectedResourceType, setSelectedResourceType] = useState<string>('all');
  const [resourceLimit, setResourceLimit] = useState(10);
  const [compartments, setCompartments] = useState<any[]>([]);

  // Load compartments on mount
  useEffect(() => {
    const fetchCompartments = async () => {
      try {
        const data = await cloudService.getCompartments();
        setCompartments(data);
      } catch (err) {
        console.error('Failed to load compartments', err);
      }
    };
    fetchCompartments();
  }, []);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Parallel loading for performance
      const [healthData, analysisData, topResourcesData, insightsData, recommendationsData] = await Promise.all([
        costAnalyzerService.getHealthCheck(),
        costAnalyzerService.analyzeCosts({
          period: selectedPeriod,
          include_forecasting: true,
          include_optimization: true,
          include_anomaly_detection: true,
          compartment_ids: selectedCompartment === 'all' ? undefined : [selectedCompartment],
          resource_types: selectedResourceType === 'all' ? undefined : [selectedResourceType]
        }),
        costAnalyzerService.getTopCostlyResources({
          limit: resourceLimit,
          period: selectedPeriod,
          compartment_id: selectedCompartment === 'all' ? undefined : selectedCompartment,
          resource_types: selectedResourceType === 'all' ? undefined : [selectedResourceType]
        }),
        costAnalyzerService.getCostInsightsSummary(selectedPeriod),
        costAnalyzerService.getPriorityRecommendations(5)
      ]);

      setHealthCheck(healthData);
      setCostAnalysis(analysisData);
      setTopResources(topResourcesData);
      setInsights(insightsData);
      setRecommendations(recommendationsData);

    } catch (err: any) {
      console.error('Failed to load cost data:', err);
      setError(err.message || 'Failed to load analysis data');
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod, selectedCompartment, selectedResourceType, resourceLimit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleExport = (format: 'pdf' | 'csv') => {
    alert(`Export to ${format.toUpperCase()} initiated...`);
  };

  if (loading) return <div className="h-screen flex items-center justify-center"><LoadingSpinner size="lg" message="Analyzing Financial Data..." /></div>;
  if (error) return <div className="p-8 text-center text-red-500">Error: {error} <button onClick={loadData} className="underline ml-2">Retry</button></div>;

  return (
    <div className="space-y-8 pb-12 w-full max-w-full animate-fade-in">

      {/* Hero Section */}
      {insights && (
        <FinOpsHero
          totalCost={insights.total_cost}
          currency={insights.currency}
          healthScore={insights.cost_health_score}
          period={selectedPeriod}
        />
      )}

      {/* Control Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="form-select text-sm rounded-lg border-gray-200 dark:bg-gray-700 dark:border-gray-600 focus:ring-emerald-500"
          >
            <option value="mtd">Month-to-Date</option>
            <option value="last_30_days">Last 30 Days</option>
            <option value="last_90_days">Last 90 Days</option>
            <option value="last_month">Previous Month</option>
            <option value="daily">Today</option>
            <option value="yearly">Last 12 Months</option>
          </select>

          <select
            value={selectedCompartment}
            onChange={(e) => setSelectedCompartment(e.target.value)}
            className="form-select text-sm rounded-lg border-gray-200 dark:bg-gray-700 dark:border-gray-600 focus:ring-emerald-500"
          >
            <option value="all">All Compartments</option>
            {compartments.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

          <button
            onClick={loadData}
            className="p-2 text-gray-500 hover:text-emerald-500 transition-colors"
            title="Refresh Data"
          >
            <i className="fas fa-sync-alt"></i>
          </button>
        </div>

        <div className="flex gap-2">
          <button onClick={() => handleExport('csv')} className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
            <i className="fas fa-file-csv mr-2"></i>Export CSV
          </button>
        </div>

        {/* Data Source Badge */}
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
            <i className="fas fa-database text-emerald-500"></i>
            Source: OCI Usage API
          </span>
          <span className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
            <i className="fas fa-check-circle text-blue-500"></i>
            Actual Costs Only
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      {insights && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassStatCard title="Total Spend" value={costAnalyzerService.formatCurrency(insights.total_cost)} icon="fas fa-dollar-sign" color="emerald" />
          <GlassStatCard title="Optimization Potential" value={costAnalyzerService.formatCurrency(insights.optimization_potential)} icon="fas fa-piggy-bank" color="blue" />
          <GlassStatCard title="Active Anomalies" value={insights.anomaly_count} subValue={insights.anomaly_count > 0 ? "Requires Review" : "Systems Normal"} icon="fas fa-bolt" color="orange" />
          <GlassStatCard title="High Priority Recs" value={insights.high_priority_recommendations} subValue="Immediate Action" icon="fas fa-check-double" color="red" />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {[
            { id: 'overview', name: 'Overview & Trends', icon: 'fas fa-chart-area' },
            { id: 'resources', name: 'Top Spenders', icon: 'fas fa-list-ol' },
            { id: 'recommendations', name: 'Optimization Plan', icon: 'fas fa-magic' },
            { id: 'anomalies', name: 'Anomalies', icon: 'fas fa-exclamation-circle' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-all
                ${activeTab === tab.id
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <i className={`${tab.icon} mr-3 ${activeTab === tab.id ? 'text-emerald-500' : 'text-gray-400 group-hover:text-gray-500'}`}></i>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && costAnalysis?.cost_trends && (
          <div className="space-y-6">
            <CostTrendChart trends={costAnalysis.cost_trends} />

            {/* Charts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Chart 1: By Compartment */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                  <i className="fas fa-layer-group text-blue-500 mr-2"></i>
                  Cost by Compartment
                </h3>
                {costAnalysis.compartment_breakdown ? (
                  <DonutChart data={costAnalysis.compartment_breakdown.map(c => ({ name: c.compartment_name, value: c.total_cost }))} />
                ) : (
                  <div className="text-center text-gray-400 py-8">No breakdown available</div>
                )}
              </div>

              {/* Chart 2: By Resource Type */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                  <i className="fas fa-cubes text-emerald-500 mr-2"></i>
                  Cost by Resource
                </h3>
                {topResources?.resources ? (
                  (() => {
                    // Aggregate by type
                    const typeMap = new Map<string, number>();
                    topResources.resources.forEach(r => {
                      const type = r.resource.resource_type || 'Unknown';
                      typeMap.set(type, (typeMap.get(type) || 0) + r.resource.cost_amount);
                    });
                    const typeData = Array.from(typeMap.entries()).map(([name, value]) => ({ name, value }));
                    return <DonutChart data={typeData} />;
                  })()
                ) : (
                  <div className="text-center text-gray-400 py-8">No resource data available</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'resources' && topResources && (
          <TopResourcesTable resources={topResources.resources} />
        )}

        {activeTab === 'recommendations' && (
          (recommendations?.recommendations && recommendations.recommendations.length > 0) ? (
            <RecommendationsPanel recommendations={recommendations.recommendations} />
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-12 text-center border border-gray-100 dark:border-gray-700">
              <i className="fas fa-magic text-5xl text-gray-300 mb-4"></i>
              <h3 className="text-xl font-bold text-gray-600 dark:text-gray-300 mb-2">Optimization Recommendations</h3>
              <p className="text-gray-400 max-w-md mx-auto">
                AI-powered cost optimization recommendations require integration with OCI Cloud Advisor.
                This feature is coming soon.
              </p>
            </div>
          )
        )}

        {activeTab === 'anomalies' && (
          (costAnalysis?.anomalies && costAnalysis.anomalies.length > 0) ? (
            <AnomaliesPanel anomalies={costAnalysis.anomalies} />
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-12 text-center border border-gray-100 dark:border-gray-700">
              <i className="fas fa-chart-line text-5xl text-gray-300 mb-4"></i>
              <h3 className="text-xl font-bold text-gray-600 dark:text-gray-300 mb-2">Cost Anomaly Detection</h3>
              <p className="text-gray-400 max-w-md mx-auto">
                Intelligent anomaly detection using ML analysis of cost trends is under development.
                No anomalies detected for the current period.
              </p>
            </div>
          )
        )}
      </div>

    </div>
  );
}