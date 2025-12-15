import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { LoadingSpinner } from './LoadingSpinner';
import { AllResourcesResponse } from '../../services/cloudService';

interface MetricsChartProps {
  title: string;
  type: 'health' | 'distribution';
  data: AllResourcesResponse | null | undefined;
  loading: boolean;
}

export function MetricsChart({ title, type, data, loading }: MetricsChartProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-transparent dark:from-blue-900/10" />
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 relative z-10 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-3">
            <i className="fas fa-chart-pie text-white text-sm" />
          </div>
          {title}
        </h3>
        <div className="h-72 flex items-center justify-center relative z-10">
          <LoadingSpinner size="lg" message="Loading metrics..." />
        </div>
      </div>
    );
  }

  if (!data || !data.resources) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-transparent dark:from-gray-900/10" />
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 relative z-10 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center mr-3">
            <i className="fas fa-chart-pie text-white text-sm" />
          </div>
          {title}
        </h3>
        <div className="h-72 flex flex-col items-center justify-center relative z-10">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
            <i className="fas fa-chart-pie text-3xl text-gray-300 dark:text-gray-500" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No data available</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Select a compartment to view metrics</p>
        </div>
      </div>
    );
  }

  const generateHealthData = () => {
    const allResources = Object.values(data.resources).flat();
    const healthyCount = allResources.filter(r => r.lifecycle_state === 'ACTIVE' || r.lifecycle_state === 'RUNNING' || r.lifecycle_state === 'AVAILABLE').length;
    const stoppedCount = allResources.filter(r => r.lifecycle_state === 'STOPPED' || r.lifecycle_state === 'INACTIVE').length;
    const errorCount = allResources.filter(r => r.lifecycle_state === 'FAILED' || r.lifecycle_state === 'ERROR').length;
    const otherCount = allResources.length - healthyCount - stoppedCount - errorCount;

    const healthData = [];
    if (healthyCount > 0) healthData.push({ name: 'Healthy', value: healthyCount, color: '#10B981', icon: 'fa-check-circle' });
    if (stoppedCount > 0) healthData.push({ name: 'Stopped', value: stoppedCount, color: '#F59E0B', icon: 'fa-pause-circle' });
    if (errorCount > 0) healthData.push({ name: 'Error', value: errorCount, color: '#EF4444', icon: 'fa-exclamation-circle' });
    if (otherCount > 0) healthData.push({ name: 'Other', value: otherCount, color: '#6B7280', icon: 'fa-question-circle' });

    return healthData;
  };

  const generateDistributionData = () => {
    const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899', '#06B6D4', '#14B8A6'];
    return Object.entries(data.resources).map(([type, resources], index) => ({
      name: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      count: resources.length,
      color: colors[index % colors.length],
      healthy: resources.filter(r => r.lifecycle_state === 'ACTIVE' || r.lifecycle_state === 'RUNNING' || r.lifecycle_state === 'AVAILABLE').length,
      stopped: resources.filter(r => r.lifecycle_state === 'STOPPED' || r.lifecycle_state === 'INACTIVE').length,
      error: resources.filter(r => r.lifecycle_state === 'FAILED' || r.lifecycle_state === 'ERROR').length,
    }));
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl shadow-xl p-4 min-w-[150px]">
          <div className="flex items-center mb-2">
            <div
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: data.color || payload[0].fill }}
            />
            <span className="font-bold text-gray-900 dark:text-white">{data.name}</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {data.value || data.count}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            resources
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = ({ payload }: any) => (
    <div className="flex flex-wrap justify-center gap-4 mt-4">
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center">
          <div
            className="w-3 h-3 rounded-full mr-2 shadow-sm"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );

  const renderHealthChart = () => {
    const healthData = generateHealthData();

    if (healthData.length === 0) {
      return (
        <div className="h-72 flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
            <i className="fas fa-heartbeat text-3xl text-gray-300 dark:text-gray-500" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No health data available</p>
        </div>
      );
    }

    const total = healthData.reduce((sum, item) => sum + item.value, 0);

    return (
      <div className="relative">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <defs>
              {healthData.map((entry, index) => (
                <linearGradient key={`gradient-${index}`} id={`healthGradient${index}`} x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                  <stop offset="100%" stopColor={entry.color} stopOpacity={0.7} />
                </linearGradient>
              ))}
            </defs>
            <Pie
              data={healthData}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={100}
              paddingAngle={4}
              dataKey="value"
              stroke="none"
              animationBegin={0}
              animationDuration={800}
            >
              {healthData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={`url(#healthGradient${index})`}
                  style={{ filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))' }}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        {/* Center Label */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ top: '-10px' }}>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900 dark:text-white">{total}</div>
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Total</div>
          </div>
        </div>

        {/* Custom Legend */}
        <div className="flex flex-wrap justify-center gap-4 mt-2">
          {healthData.map((entry, index) => (
            <div key={index} className="flex items-center bg-gray-50 dark:bg-gray-700/50 px-3 py-1.5 rounded-lg">
              <div
                className="w-2.5 h-2.5 rounded-full mr-2"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{entry.name}</span>
              <span className="ml-2 text-sm font-bold text-gray-900 dark:text-white">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderDistributionChart = () => {
    const distributionData = generateDistributionData().filter(d => d.count > 0);

    if (distributionData.length === 0) {
      return (
        <div className="h-72 flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
            <i className="fas fa-chart-bar text-3xl text-gray-300 dark:text-gray-500" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No distribution data available</p>
        </div>
      );
    }

    return (
      <div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={distributionData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            barSize={40}
          >
            <defs>
              <linearGradient id="barGradientHealthy" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10B981" stopOpacity={1} />
                <stop offset="100%" stopColor="#059669" stopOpacity={0.8} />
              </linearGradient>
              <linearGradient id="barGradientStopped" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F59E0B" stopOpacity={1} />
                <stop offset="100%" stopColor="#D97706" stopOpacity={0.8} />
              </linearGradient>
              <linearGradient id="barGradientError" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={1} />
                <stop offset="100%" stopColor="#DC2626" stopOpacity={0.8} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" opacity={0.5} />
            <XAxis
              dataKey="name"
              stroke="#9CA3AF"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              angle={-45}
              textAnchor="end"
              height={60}
              interval={0}
            />
            <YAxis
              stroke="#9CA3AF"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.05)', radius: 8 }} />
            <Bar
              dataKey="healthy"
              stackId="a"
              fill="url(#barGradientHealthy)"
              name="Healthy"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="stopped"
              stackId="a"
              fill="url(#barGradientStopped)"
              name="Stopped"
            />
            <Bar
              dataKey="error"
              stackId="a"
              fill="url(#barGradientError)"
              name="Error"
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>

        {/* Custom Legend */}
        <div className="flex justify-center gap-6 mt-2">
          {[
            { name: 'Healthy', color: '#10B981' },
            { name: 'Stopped', color: '#F59E0B' },
            { name: 'Error', color: '#EF4444' }
          ].map((item, index) => (
            <div key={index} className="flex items-center">
              <div
                className="w-3 h-3 rounded mr-2"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const getIcon = () => type === 'health' ? 'fa-heartbeat' : 'fa-chart-bar';
  const getGradient = () => type === 'health'
    ? 'from-emerald-500 to-teal-600'
    : 'from-blue-500 to-indigo-600';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 relative overflow-hidden group hover:shadow-lg transition-all duration-300">
      {/* Background Decoration */}
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${getGradient()} rounded-full mix-blend-multiply filter blur-3xl opacity-5 group-hover:opacity-10 transition-opacity`} />

      {/* Header */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${getGradient()} flex items-center justify-center shadow-lg mr-3`}>
            <i className={`fas ${getIcon()} text-white`} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {data.total_resources} total resources
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400 dark:text-gray-500">
            Last updated
          </div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
            {new Date(data.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="relative z-10">
        {type === 'health' ? renderHealthChart() : renderDistributionChart()}
      </div>
    </div>
  );
}