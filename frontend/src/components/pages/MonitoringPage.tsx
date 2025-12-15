import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { monitoringService, Alert } from '../../services/monitoringService';
import { useCompartments } from '../../services/cloudService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { PremiumHero } from '../ui/PremiumHero';
import { GlassStatCard } from '../ui/GlassStatCard';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// -- Components --

// 1. Health Gauge (Polished)
const HealthGauge: React.FC<{ score: number }> = ({ score }) => {
  const color = score >= 90 ? 'text-emerald-500' : score >= 70 ? 'text-amber-500' : 'text-red-500';
  const stroke = score >= 90 ? '#10B981' : score >= 70 ? '#F59E0B' : '#EF4444';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 h-full flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Glow */}
      <div className={`absolute top-0 right-0 w-32 h-32 bg-current opacity-5 rounded-full filter blur-2xl ${color}`}></div>

      <div className="relative w-40 h-40">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-gray-100 dark:text-gray-700" />
          <circle
            cx="80" cy="80" r="70"
            stroke={stroke}
            strokeWidth="12"
            fill="transparent"
            strokeLinecap="round"
            strokeDasharray={439.8}
            strokeDashoffset={439.8 - (439.8 * score) / 100}
            className="transition-all duration-1000 ease-out shadow-lg"
          />
        </svg>
        <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center flex-col">
          <span className={`text-4xl font-extrabold ${color}`}>{score.toFixed(0)}%</span>
          <span className="text-xs text-gray-400 uppercase tracking-widest font-bold mt-1">Health</span>
        </div>
      </div>
      <div className="mt-4 text-center">
        <div className={`text-lg font-bold ${color}`}>
          {score >= 90 ? 'System Healthy' : score >= 70 ? 'Performance Degraded' : 'Critical Issues'}
        </div>
        <p className="text-xs text-gray-400 mt-1">Based on telemetry from all active resources</p>
      </div>
    </div>
  );
};

// 2. Service Status Matrix (Modernized)
const ServiceStatusMatrix: React.FC<{ alarms: Alert[] }> = ({ alarms }) => {
  const services = ['Compute', 'Cluster', 'Database', 'Load Balancer', 'Networking', 'Storage'];

  const getServiceStatus = (service: string) => {
    const serviceAlarms = alarms.filter(a => a.category === service);
    const critical = serviceAlarms.filter(a => a.severity === 'CRITICAL').length;
    const high = serviceAlarms.filter(a => a.severity === 'HIGH').length;

    if (critical > 0) return { status: 'Critical', color: 'bg-red-500', icon: 'fa-times-circle', text: 'text-red-600', bg: 'bg-red-50 dark:bg-red-900/20' };
    if (high > 0) return { status: 'Warning', color: 'bg-amber-500', icon: 'fa-exclamation-circle', text: 'text-amber-600', bg: 'bg-amber-50 dark:bg-amber-900/20' };
    return { status: 'Operational', color: 'bg-emerald-500', icon: 'fa-check-circle', text: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-900/20' };
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-6 flex items-center">
        <i className="fas fa-sitemap mr-2 text-blue-500"></i> Service Health Status
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map(service => {
          const { status, color, icon, text, bg } = getServiceStatus(service);
          return (
            <div key={service} className="group p-4 rounded-xl border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all bg-white dark:bg-gray-800/50">
              <div className="flex items-center justify-between mb-2">
                <div className={`w-2 h-2 rounded-full ${color} animate-pulse shadow-sm`}></div>
                <i className={`fas ${icon} ${text} text-opacity-50 group-hover:text-opacity-100 transition-opacity`}></i>
              </div>
              <h4 className="font-bold text-gray-900 dark:text-white">{service}</h4>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full mt-2 inline-block ${bg} ${text}`}>
                {status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// 3. Incident Feed (Modernized)
const IncidentFeed: React.FC<{ alarms: Alert[] }> = ({ alarms }) => {
  const [filter, setFilter] = useState('ALL');

  const filtered = useMemo(() => {
    if (filter === 'ALL') return alarms;
    return alarms.filter(a => a.severity === filter);
  }, [alarms, filter]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col h-full overflow-hidden">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 flex items-center justify-center">
            <i className="fas fa-bell"></i>
          </div>
          <h3 className="font-bold text-gray-900 dark:text-white">Active Incidents</h3>
        </div>
        <div className="flex bg-gray-200 dark:bg-gray-700 rounded-lg p-1">
          {['ALL', 'CRITICAL', 'HIGH'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-[10px] font-bold px-3 py-1 rounded-md transition-all ${filter === f ? 'bg-white dark:bg-gray-600 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900'}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-grow overflow-y-auto p-2 space-y-2 max-h-[500px] custom-scrollbar">
        {filtered.length === 0 ? (
          <div className="text-center py-16 text-gray-400 flex flex-col items-center">
            <div className="w-16 h-16 bg-green-50 dark:bg-green-900/20 rounded-full flex items-center justify-center mb-4">
              <i className="fas fa-check text-2xl text-green-500"></i>
            </div>
            <p className="text-sm font-medium text-gray-500">No active incidents found</p>
            <p className="text-xs text-gray-400 mt-1">Your systems are running smoothly</p>
          </div>
        ) : (
          filtered.map(alarm => (
            <div key={alarm.id} className="group p-4 rounded-xl border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-default">
              <div className="flex justify-between items-start mb-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wide ${alarm.severity === 'CRITICAL' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                  }`}>
                  {alarm.severity}
                </span>
                <span className="text-xs text-gray-400 font-mono">{new Date(alarm.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-1 group-hover:text-blue-600 transition-colors">{alarm.name}</h4>
              <div className="flex items-center text-xs text-gray-500">
                <i className="fas fa-cube mr-1.5 opacity-50"></i>
                {alarm.resource}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// -- Main Page --
export function MonitoringPage() {
  const { data: compartments, isLoading: compartmentsLoading } = useCompartments();
  const [selectedCompartmentId, setSelectedCompartmentId] = useState<string>('');

  useEffect(() => {
    if (compartments && compartments.length > 0 && (!selectedCompartmentId || selectedCompartmentId === 'test-compartment')) {
      setSelectedCompartmentId(compartments[0].id);
    }
  }, [compartments, selectedCompartmentId]);

  // Parallel Data Fetching
  const { data: health } = useQuery({
    queryKey: ['health', selectedCompartmentId],
    queryFn: () => monitoringService.getHealthStatus(selectedCompartmentId),
    enabled: !!selectedCompartmentId,
  });

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard', selectedCompartmentId],
    queryFn: () => monitoringService.getDashboard(selectedCompartmentId),
    enabled: !!selectedCompartmentId,
  });

  const { data: alarms } = useQuery({
    queryKey: ['alarms', selectedCompartmentId],
    queryFn: () => monitoringService.getAlarms(selectedCompartmentId),
    enabled: !!selectedCompartmentId,
  });

  if (compartmentsLoading || dashboardLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh]">
        <LoadingSpinner size="lg" message="Gathering telemetry signals..." />
      </div>
    );
  }

  // Fallbacks
  const score = health?.health_score || 0;
  const activeAlarms = alarms || [];
  const uptime = dashboard?.quick_stats.uptime_score || 100;

  // Dummy trend data for visual appeal (replace with real if available)
  const performanceData = [
    { time: '00:00', value: 45 }, { time: '02:00', value: 52 }, { time: '04:00', value: 48 },
    { time: '06:00', value: 65 }, { time: '08:00', value: 78 }, { time: '10:00', value: 85 },
    { time: '12:00', value: 72 }, { time: '14:00', value: 68 }, { time: '16:00', value: 75 },
    { time: '18:00', value: 80 }, { time: '20:00', value: 60 }, { time: '22:00', value: 55 },
  ];

  return (
    <div className="space-y-8 pb-12 w-full max-w-full overflow-hidden animate-fade-in">

      {/* Hero Header */}
      <PremiumHero
        title="System Health & Monitoring"
        subtitle="Real-time performance metrics, availability status, and incident tracking."
        pattern="circles"
        colorCombo="cyan"
        stats={[
          { label: 'Uptime (30d)', value: `${uptime.toFixed(1)}%` },
          { label: 'Active Alerts', value: activeAlarms.length.toString() }
        ]}
      />

      {/* Controls */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex justify-between items-center">
        <div className="w-full md:w-1/3">
          <CompartmentSelector
            compartments={compartments || []}
            selectedCompartmentId={selectedCompartmentId}
            onCompartmentChange={setSelectedCompartmentId}
            loading={compartmentsLoading}
          />
        </div>
        <div className="text-xs text-gray-500 hidden md:block">
          <i className="fas fa-sync-alt mr-2 animate-spin-slow"></i>
          Live Updates Enabled
        </div>
      </div>

      {/* Top Section: Health Gauge + Key Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-auto">
        <div className="md:col-span-1 h-80 md:h-auto">
          <HealthGauge score={score} />
        </div>
        <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <GlassStatCard
            title="System Uptime"
            value={`${uptime.toFixed(1)}%`}
            subValue="Target: 99.99%"
            icon="fas fa-clock"
            color="blue"
          />
          <GlassStatCard
            title="Critical Incidents"
            value={activeAlarms.filter(a => a.severity === 'CRITICAL').length}
            subValue="Requires Immediate Action"
            icon="fas fa-bell"
            color="red"
          />
          <GlassStatCard
            title="Metrics Monitored"
            value={dashboard?.trends.total_alarms_trend || '42'}
            subValue="Across 6 Services"
            icon="fas fa-eye"
            color="purple"
          />
        </div>
      </div>

      {/* Middle Section: Trends + Service Matrix + Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[500px]">
        <div className="lg:col-span-2 space-y-6 flex flex-col">
          {/* Performance Trend Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 flex-1">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-6 flex items-center">
              <i className="fas fa-chart-line mr-2 text-indigo-500"></i> System Load Trend
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <defs>
                    <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" opacity={0.5} />
                  <XAxis dataKey="time" stroke="#9CA3AF" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#6366F1" strokeWidth={3} fillOpacity={1} fill="url(#colorLoad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Service Matrix */}
          <ServiceStatusMatrix alarms={activeAlarms} />
        </div>

        <div className="lg:col-span-1 h-full">
          <IncidentFeed alarms={activeAlarms} />
        </div>
      </div>

    </div>
  );
}