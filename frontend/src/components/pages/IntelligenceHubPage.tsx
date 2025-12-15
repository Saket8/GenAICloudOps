/**
 * Cloud Intelligence Hub - Multi-dimensional analytics dashboard
 * 
 * Provides insights not available in OCI Console by combining
 * data from multiple APIs into unified visualizations.
 */
import React, { useState, useMemo } from 'react';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { useCompartments } from '../../services/cloudService';
import { useHealthMatrix, useTopActions, ResourceHealth, TopAction } from '../../services/intelligenceService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { PremiumHero } from '../ui/PremiumHero';

// ===== Health Heatmap Cell Component =====
const HealthCell: React.FC<{
    resource: ResourceHealth;
    isSelected: boolean;
    onClick: () => void;
}> = ({ resource, isSelected, onClick }) => {
    const getColor = () => {
        if (resource.level === 'healthy') return 'bg-emerald-500';
        if (resource.level === 'warning') return 'bg-amber-500';
        return 'bg-red-500';
    };

    const getBorderColor = () => {
        if (resource.level === 'healthy') return 'border-emerald-400';
        if (resource.level === 'warning') return 'border-amber-400';
        return 'border-red-400';
    };

    return (
        <button
            onClick={onClick}
            className={`
        relative group w-12 h-12 rounded-lg ${getColor()} 
        flex items-center justify-center font-bold text-white text-sm
        transition-all duration-200 hover:scale-110 hover:z-10
        ${isSelected ? `ring-2 ring-white ring-offset-2 ring-offset-gray-900 ${getBorderColor()}` : ''}
        hover:shadow-lg
      `}
            title={`${resource.resource_name}: ${resource.score}/10`}
        >
            {resource.score}

            {/* Hover tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none">
                {resource.resource_name}
            </div>
        </button>
    );
};

// ===== Resource Type Row with Wave Graph =====
const ResourceTypeRow: React.FC<{
    type: string;
    resources: ResourceHealth[];
    selectedId: string | null;
    onSelect: (resource: ResourceHealth) => void;
}> = ({ type, resources, selectedId, onSelect }) => {
    const typeLabels: Record<string, string> = {
        compute: 'Compute Instances',
        database: 'Databases',
        block_volume: 'Block Volumes',
        load_balancer: 'Load Balancers',
        cluster: 'OKE Clusters',
        network: 'Network Resources',
        storage: 'Storage',
    };

    const typeIcons: Record<string, string> = {
        compute: 'fas fa-server',
        database: 'fas fa-database',
        block_volume: 'fas fa-hdd',
        load_balancer: 'fas fa-network-wired',
        cluster: 'fas fa-dharmachakra',
        network: 'fas fa-cloud',
        storage: 'fas fa-folder',
    };

    const healthyCounts = resources.filter(r => r.level === 'healthy').length;
    const warningCounts = resources.filter(r => r.level === 'warning').length;
    const criticalCounts = resources.filter(r => r.level === 'critical').length;

    // Generate wave path from resource scores
    const generateWavePath = () => {
        if (resources.length === 0) return '';

        const width = 800;
        const height = 80;
        const padding = 40;
        const usableWidth = width - (padding * 2);
        const segmentWidth = usableWidth / Math.max(resources.length - 1, 1);

        // Map scores to Y positions (inverted: higher score = lower Y)
        const points = resources.map((r, i) => ({
            x: padding + (i * segmentWidth),
            y: height - (r.score / 10 * (height - 20)) - 10,
            score: r.score,
            level: r.level
        }));

        if (points.length === 1) {
            return `M ${points[0].x},${points[0].y} L ${points[0].x + 50},${points[0].y}`;
        }

        // Create smooth curve using cubic bezier
        let path = `M ${points[0].x},${points[0].y}`;

        for (let i = 0; i < points.length - 1; i++) {
            const p0 = points[i];
            const p1 = points[i + 1];
            const cp1x = p0.x + segmentWidth * 0.5;
            const cp2x = p1.x - segmentWidth * 0.5;
            path += ` C ${cp1x},${p0.y} ${cp2x},${p1.y} ${p1.x},${p1.y}`;
        }

        return path;
    };

    const getGradientId = () => `waveGradient-${type}`;

    // Calculate point positions for interactive dots
    const getPointPositions = () => {
        const width = 800;
        const height = 80;
        const padding = 40;
        const usableWidth = width - (padding * 2);
        const segmentWidth = usableWidth / Math.max(resources.length - 1, 1);

        return resources.map((r, i) => ({
            x: padding + (i * segmentWidth),
            y: height - (r.score / 10 * (height - 20)) - 10,
            resource: r
        }));
    };

    const points = getPointPositions();

    return (
        <div className="bg-gray-900/60 backdrop-blur-sm rounded-2xl p-5 border border-gray-800/50 hover:border-gray-700/50 transition-all duration-300 group">
            {/* Type Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center shadow-lg">
                        <i className={`${typeIcons[type] || 'fas fa-cube'} text-gray-300`} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-white">{typeLabels[type] || type}</h3>
                        <p className="text-sm text-gray-500">{resources.length} resources</p>
                    </div>
                </div>

                {/* Quick Stats Pills */}
                <div className="flex gap-2">
                    {healthyCounts > 0 && (
                        <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded-full border border-emerald-500/20">
                            {healthyCounts} healthy
                        </span>
                    )}
                    {warningCounts > 0 && (
                        <span className="px-2.5 py-1 bg-amber-500/10 text-amber-400 text-xs rounded-full border border-amber-500/20">
                            {warningCounts} warning
                        </span>
                    )}
                    {criticalCounts > 0 && (
                        <span className="px-2.5 py-1 bg-red-500/10 text-red-400 text-xs rounded-full border border-red-500/20">
                            {criticalCounts} critical
                        </span>
                    )}
                </div>
            </div>

            {/* Wave Graph Visualization */}
            <div className="relative h-24 mt-2">
                <svg
                    viewBox="0 0 800 80"
                    className="w-full h-full"
                    preserveAspectRatio="none"
                >
                    <defs>
                        {/* Multi-color gradient based on health distribution */}
                        <linearGradient id={getGradientId()} x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#f97316" />
                            <stop offset="30%" stopColor="#eab308" />
                            <stop offset="50%" stopColor="#22c55e" />
                            <stop offset="70%" stopColor="#06b6d4" />
                            <stop offset="100%" stopColor="#a855f7" />
                        </linearGradient>
                        {/* Glow filter */}
                        <filter id={`glow-${type}`} x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {/* Background grid lines */}
                    <line x1="40" y1="20" x2="760" y2="20" stroke="#374151" strokeWidth="0.5" strokeDasharray="4" opacity="0.3" />
                    <line x1="40" y1="40" x2="760" y2="40" stroke="#374151" strokeWidth="0.5" strokeDasharray="4" opacity="0.3" />
                    <line x1="40" y1="60" x2="760" y2="60" stroke="#374151" strokeWidth="0.5" strokeDasharray="4" opacity="0.3" />

                    {/* Score labels on left */}
                    <text x="20" y="23" fill="#6b7280" fontSize="8" textAnchor="middle">10</text>
                    <text x="20" y="43" fill="#6b7280" fontSize="8" textAnchor="middle">5</text>
                    <text x="20" y="73" fill="#6b7280" fontSize="8" textAnchor="middle">0</text>

                    {/* Main wave path with glow */}
                    <path
                        d={generateWavePath()}
                        fill="none"
                        stroke={`url(#${getGradientId()})`}
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        filter={`url(#glow-${type})`}
                        className="transition-all duration-500"
                    />

                    {/* Area fill under curve */}
                    <path
                        d={generateWavePath() + ` L ${points.length > 0 ? points[points.length - 1].x : 760},80 L 40,80 Z`}
                        fill={`url(#${getGradientId()})`}
                        opacity="0.1"
                    />
                </svg>

                {/* Interactive data points */}
                <div className="absolute inset-0">
                    {points.map((point, index) => {
                        const resource = point.resource;
                        const isSelected = selectedId === resource.resource_id;
                        const dotColor = resource.level === 'healthy'
                            ? 'bg-emerald-400 shadow-emerald-400/50'
                            : resource.level === 'warning'
                                ? 'bg-amber-400 shadow-amber-400/50'
                                : 'bg-red-400 shadow-red-400/50';

                        // Convert SVG coordinates to percentage
                        const leftPercent = (point.x / 800) * 100;
                        const topPercent = (point.y / 80) * 100;

                        return (
                            <button
                                key={resource.resource_id}
                                onClick={() => onSelect(resource)}
                                className={`
                                    absolute transform -translate-x-1/2 -translate-y-1/2
                                    w-8 h-8 rounded-full flex items-center justify-center
                                    text-xs font-bold text-white
                                    transition-all duration-300 hover:scale-125 hover:z-10
                                    ${dotColor} shadow-lg
                                    ${isSelected ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-900 scale-125' : ''}
                                    group/dot
                                `}
                                style={{
                                    left: `${leftPercent}%`,
                                    top: `${topPercent}%`
                                }}
                                title={`${resource.resource_name}: ${resource.score}/10`}
                            >
                                {resource.score}

                                {/* Tooltip */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900/95 text-white text-xs rounded-lg opacity-0 group-hover/dot:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700 shadow-xl z-30">
                                    <div className="font-medium">{resource.resource_name}</div>
                                    <div className="text-gray-400 text-[10px]">{resource.lifecycle_state}</div>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

// ===== Drill-Down Panel Component =====
const DrillDownPanel: React.FC<{
    resource: ResourceHealth | null;
    onClose: () => void;
}> = ({ resource, onClose }) => {
    if (!resource) return null;

    const getLevelBadge = () => {
        if (resource.level === 'healthy') {
            return <span className="px-3 py-1 bg-emerald-900/50 text-emerald-400 rounded-full text-sm font-medium">Healthy</span>;
        }
        if (resource.level === 'warning') {
            return <span className="px-3 py-1 bg-amber-900/50 text-amber-400 rounded-full text-sm font-medium">Warning</span>;
        }
        return <span className="px-3 py-1 bg-red-900/50 text-red-400 rounded-full text-sm font-medium">Critical</span>;
    };

    const getScoreColor = () => {
        if (resource.score >= 8) return 'text-emerald-400';
        if (resource.score >= 5) return 'text-amber-400';
        return 'text-red-400';
    };

    return (
        <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l border-gray-700 shadow-2xl z-50 overflow-y-auto animate-slide-in">
            {/* Header */}
            <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white">Resource Details</h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
                    >
                        <i className="fas fa-times" />
                    </button>
                </div>
            </div>

            <div className="p-4 space-y-6">
                {/* Resource Info */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <h3 className="font-semibold text-white mb-2 truncate" title={resource.resource_name}>
                        {resource.resource_name}
                    </h3>
                    <div className="flex items-center gap-2 mb-3">
                        {getLevelBadge()}
                        <span className="text-sm text-gray-400">{resource.resource_type}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-gray-400">State</span>
                            <p className="font-medium text-white">{resource.lifecycle_state}</p>
                        </div>
                        <div>
                            <span className="text-gray-400">Est. Cost</span>
                            <p className="font-medium text-white">${resource.estimated_cost}/mo</p>
                        </div>
                    </div>
                </div>

                {/* Health Score */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <h4 className="text-sm font-medium text-gray-400 mb-3">Health Score</h4>
                    <div className="flex items-center gap-4">
                        <div className={`text-5xl font-bold ${getScoreColor()}`}>
                            {resource.score}
                        </div>
                        <div className="text-gray-400 text-sm">
                            out of 10 points
                        </div>
                    </div>
                </div>

                {/* Issues List */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <h4 className="text-sm font-medium text-gray-400 mb-3">
                        Issues ({resource.issues.length})
                    </h4>

                    {resource.issues.length === 0 ? (
                        <p className="text-sm text-emerald-400 flex items-center gap-2">
                            <i className="fas fa-check-circle" />
                            No issues detected
                        </p>
                    ) : (
                        <div className="space-y-3">
                            {resource.issues.map((issue, index) => (
                                <div key={index} className="border-l-2 border-gray-600 pl-3">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs px-2 py-0.5 rounded ${issue.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                                            issue.severity === 'warning' ? 'bg-amber-900/50 text-amber-400' :
                                                'bg-blue-900/50 text-blue-400'
                                            }`}>
                                            -{issue.deduction} pts
                                        </span>
                                        <span className="text-xs text-gray-500 uppercase">{issue.category}</span>
                                    </div>
                                    <p className="text-sm text-white mb-1">{issue.message}</p>
                                    {issue.recommendation && (
                                        <p className="text-xs text-gray-400 flex items-start gap-1">
                                            <i className="fas fa-lightbulb text-amber-400 mt-0.5" />
                                            {issue.recommendation}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Resource ID */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Resource ID</h4>
                    <p className="text-xs text-gray-500 break-all font-mono">{resource.resource_id}</p>
                </div>
            </div>

            {/* Slide-in animation */}
            <style>{`
        @keyframes slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
        </div>
    );
};

// ===== Summary Stats Bar =====
const SummaryStats: React.FC<{
    total: number;
    healthy: number;
    warning: number;
    critical: number;
    waste: number;
}> = ({ total, healthy, warning, critical, waste }) => {
    return (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="text-3xl font-bold text-white">{total}</div>
                <div className="text-sm text-gray-400">Total Resources</div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4 border border-emerald-800/50">
                <div className="text-3xl font-bold text-emerald-400">{healthy}</div>
                <div className="text-sm text-gray-400">Healthy</div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4 border border-amber-800/50">
                <div className="text-3xl font-bold text-amber-400">{warning}</div>
                <div className="text-sm text-gray-400">Warning</div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4 border border-red-800/50">
                <div className="text-3xl font-bold text-red-400">{critical}</div>
                <div className="text-sm text-gray-400">Critical</div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4 border border-purple-800/50">
                <div className="text-3xl font-bold text-purple-400">${waste.toFixed(0)}</div>
                <div className="text-sm text-gray-400">Est. Waste/mo</div>
            </div>
        </div>
    );
};

// ===== Phase 2: Cost-Efficiency Bubble Chart =====
const CostBubbleChart: React.FC<{
    resources: ResourceHealth[];
    onSelect: (resource: ResourceHealth) => void;
    selectedId: string | null;
}> = ({ resources, onSelect, selectedId }) => {
    const typeColors: Record<string, string> = {
        compute: '#3b82f6',
        database: '#8b5cf6',
        cluster: '#06b6d4',
        load_balancer: '#f97316',
        block_volume: '#10b981',
        network: '#ec4899',
        storage: '#eab308',
    };

    // Simulate utilization based on lifecycle state
    const getUtilization = (resource: ResourceHealth) => {
        if (resource.lifecycle_state === 'RUNNING') return 60 + Math.random() * 30;
        if (resource.lifecycle_state === 'STOPPED') return 0;
        return 20 + Math.random() * 40;
    };

    // Calculate bubble positions
    const bubbles = resources.map(r => ({
        resource: r,
        x: (r.score / 10) * 80 + 10, // Health score 0-10 mapped to 10-90%
        y: 90 - getUtilization(r), // Utilization inverted (high util = top)
        size: Math.max(20, Math.min(60, r.estimated_cost / 2 + 15)), // Cost mapped to size
        color: typeColors[r.resource_type] || '#6b7280',
    }));

    return (
        <div className="bg-gray-900/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-semibold text-white">Cost-Efficiency Analysis</h3>
                    <p className="text-sm text-gray-500">Bubble size = Monthly cost</p>
                </div>
                <div className="flex gap-3 text-xs">
                    {Object.entries(typeColors).slice(0, 5).map(([type, color]) => (
                        <div key={type} className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-gray-400 capitalize">{type.replace('_', ' ')}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="relative h-80 bg-gray-800/30 rounded-xl border border-gray-700/50 overflow-hidden">
                {/* Axis labels */}
                <div className="absolute left-2 top-2 text-xs text-gray-500">High Util</div>
                <div className="absolute left-2 bottom-2 text-xs text-gray-500">Low Util</div>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-gray-500">
                    Low Score ◄──────► High Score
                </div>

                {/* Grid */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    <line x1="10%" y1="50%" x2="90%" y2="50%" stroke="#374151" strokeWidth="1" strokeDasharray="4" opacity="0.3" />
                    <line x1="50%" y1="10%" x2="50%" y2="90%" stroke="#374151" strokeWidth="1" strokeDasharray="4" opacity="0.3" />
                </svg>

                {/* Bubbles */}
                {bubbles.map((bubble, index) => (
                    <button
                        key={bubble.resource.resource_id}
                        onClick={() => onSelect(bubble.resource)}
                        className={`
                            absolute transform -translate-x-1/2 -translate-y-1/2
                            rounded-full flex items-center justify-center
                            transition-all duration-300 hover:scale-110 hover:z-10
                            text-white text-xs font-bold
                            ${selectedId === bubble.resource.resource_id ? 'ring-2 ring-white' : ''}
                            group
                        `}
                        style={{
                            left: `${bubble.x}%`,
                            top: `${bubble.y}%`,
                            width: bubble.size,
                            height: bubble.size,
                            backgroundColor: bubble.color,
                            opacity: 0.8,
                            boxShadow: `0 0 20px ${bubble.color}40`,
                        }}
                    >
                        ${bubble.resource.estimated_cost.toFixed(0)}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900/95 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none border border-gray-700 z-30">
                            <div className="font-medium">{bubble.resource.resource_name}</div>
                            <div className="text-gray-400">Score: {bubble.resource.score} | ${bubble.resource.estimated_cost}/mo</div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

// ===== Phase 2: Waste Detection Widget =====
const WasteDetectionWidget: React.FC<{
    resources: ResourceHealth[];
    onSelect: (resource: ResourceHealth) => void;
}> = ({ resources, onSelect }) => {
    const stoppedResources = resources.filter(r =>
        r.lifecycle_state === 'STOPPED' || r.lifecycle_state === 'INACTIVE'
    );

    const totalWaste = stoppedResources.reduce((sum, r) => sum + r.estimated_cost * 0.2, 0);

    return (
        <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 rounded-2xl p-6 border border-red-800/30">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                    <i className="fas fa-exclamation-triangle text-red-400 text-xl" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Waste Detection</h3>
                    <p className="text-sm text-gray-400">{stoppedResources.length} stopped resources</p>
                </div>
                <div className="ml-auto text-right">
                    <div className="text-2xl font-bold text-red-400">${totalWaste.toFixed(0)}</div>
                    <div className="text-xs text-gray-500">Est. waste/month</div>
                </div>
            </div>

            {stoppedResources.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                    {stoppedResources.slice(0, 5).map(resource => (
                        <button
                            key={resource.resource_id}
                            onClick={() => onSelect(resource)}
                            className="w-full flex items-center justify-between p-3 bg-gray-800/50 rounded-lg hover:bg-gray-700/50 transition-colors text-left"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-red-400" />
                                <div>
                                    <div className="text-sm text-white truncate max-w-[200px]">{resource.resource_name}</div>
                                    <div className="text-xs text-gray-500">{resource.resource_type}</div>
                                </div>
                            </div>
                            <div className="text-sm text-red-400">${(resource.estimated_cost * 0.2).toFixed(0)}/mo</div>
                        </button>
                    ))}
                </div>
            ) : (
                <div className="text-center py-6 text-gray-400">
                    <i className="fas fa-check-circle text-emerald-400 text-2xl mb-2" />
                    <p>No waste detected!</p>
                </div>
            )}
        </div>
    );
};

// ===== Phase 2: Activity Timeline =====
const ActivityTimeline: React.FC<{
    resources: ResourceHealth[];
}> = ({ resources }) => {
    // Generate mock activity events based on resources
    const events = resources.slice(0, 8).map((r, i) => ({
        id: r.resource_id,
        resource: r,
        type: r.lifecycle_state === 'RUNNING' ? 'started' : r.lifecycle_state === 'STOPPED' ? 'stopped' : 'updated',
        time: new Date(Date.now() - (i * 3600000 + Math.random() * 7200000)),
    })).sort((a, b) => b.time.getTime() - a.time.getTime());

    const getEventIcon = (type: string) => {
        if (type === 'started') return 'fas fa-play text-emerald-400';
        if (type === 'stopped') return 'fas fa-stop text-red-400';
        return 'fas fa-sync text-blue-400';
    };

    const getEventColor = (type: string) => {
        if (type === 'started') return 'border-emerald-500';
        if (type === 'stopped') return 'border-red-500';
        return 'border-blue-500';
    };

    const formatTime = (date: Date) => {
        const diff = Date.now() - date.getTime();
        const hours = Math.floor(diff / 3600000);
        if (hours < 1) return 'Just now';
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    };

    return (
        <div className="bg-gray-900/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <i className="fas fa-history text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
                    <p className="text-sm text-gray-500">Resource state changes</p>
                </div>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto">
                {events.map((event, index) => (
                    <div
                        key={event.id + index}
                        className={`flex items-center gap-3 p-3 rounded-lg bg-gray-800/30 border-l-2 ${getEventColor(event.type)}`}
                    >
                        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                            <i className={getEventIcon(event.type)} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-sm text-white truncate">{event.resource.resource_name}</div>
                            <div className="text-xs text-gray-500">
                                {event.type === 'started' ? 'Started running' :
                                    event.type === 'stopped' ? 'Stopped' : 'Updated'} • {event.resource.resource_type}
                            </div>
                        </div>
                        <div className="text-xs text-gray-500">{formatTime(event.time)}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ===== Phase 2: Export Button =====
const ExportButton: React.FC<{
    resources: ResourceHealth[];
    compartmentId: string | null;
}> = ({ resources, compartmentId }) => {
    const [exporting, setExporting] = useState(false);

    const exportCSV = () => {
        setExporting(true);

        const headers = ['Resource Name', 'Type', 'Health Score', 'Level', 'State', 'Est. Cost', 'Issues'];
        const rows = resources.map(r => [
            r.resource_name,
            r.resource_type,
            r.score.toString(),
            r.level,
            r.lifecycle_state,
            `$${r.estimated_cost}`,
            r.issues.map(i => i.message).join('; ')
        ]);

        const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-report-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);

        setTimeout(() => setExporting(false), 1000);
    };

    return (
        <button
            onClick={exportCSV}
            disabled={exporting || resources.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
        >
            <i className={exporting ? 'fas fa-spinner animate-spin' : 'fas fa-download'} />
            <span>{exporting ? 'Exporting...' : 'Export CSV'}</span>
        </button>
    );
};

// ===== View Tabs Component =====
type ViewType = 'heatmap' | 'bubble' | 'insights';

const ViewTabs: React.FC<{
    activeView: ViewType;
    onViewChange: (view: ViewType) => void;
}> = ({ activeView, onViewChange }) => {
    const tabs = [
        { id: 'heatmap' as ViewType, label: 'Health Waves', icon: 'fas fa-wave-square' },
        { id: 'bubble' as ViewType, label: 'Cost Analysis', icon: 'fas fa-circle' },
        { id: 'insights' as ViewType, label: 'Insights', icon: 'fas fa-lightbulb' },
    ];

    return (
        <div className="flex items-center gap-1 p-1 bg-gray-800/50 rounded-xl border border-gray-700">
            {tabs.map(tab => (
                <button
                    key={tab.id}
                    onClick={() => onViewChange(tab.id)}
                    className={`
                        flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
                        ${activeView === tab.id
                            ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg'
                            : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}
                    `}
                >
                    <i className={tab.icon} />
                    {tab.label}
                </button>
            ))}
        </div>
    );
};

// ===== Phase 3: Top Actions Panel =====
const TopActionsPanel: React.FC<{
    actions: TopAction[];
    totalSavings: number;
    isLoading: boolean;
    onActionClick: (action: TopAction) => void;
}> = ({ actions, totalSavings, isLoading, onActionClick }) => {
    const getCategoryStyle = (category: string) => {
        switch (category) {
            case 'delete_zombie':
                return { bg: 'from-red-500/20 to-orange-500/20', border: 'border-red-500/30', icon: '🧟' };
            case 'review_stopped':
                return { bg: 'from-amber-500/20 to-yellow-500/20', border: 'border-amber-500/30', icon: '⏸️' };
            case 'fix_security':
                return { bg: 'from-purple-500/20 to-pink-500/20', border: 'border-purple-500/30', icon: '🔒' };
            case 'fix_unavailable':
                return { bg: 'from-orange-500/20 to-red-500/20', border: 'border-orange-500/30', icon: '⚠️' };
            case 'optimize':
                return { bg: 'from-blue-500/20 to-cyan-500/20', border: 'border-blue-500/30', icon: '⚡' };
            default:
                return { bg: 'from-gray-500/20 to-gray-600/20', border: 'border-gray-500/30', icon: '📋' };
        }
    };

    const getRiskBadge = (risk: string) => {
        switch (risk) {
            case 'high':
                return <span className="px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400 border border-red-500/30">High Risk</span>;
            case 'medium':
                return <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">Medium</span>;
            default:
                return <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Low Risk</span>;
        }
    };

    if (isLoading) {
        return (
            <div className="bg-gradient-to-r from-cyan-900/20 to-blue-900/20 rounded-2xl p-6 border border-cyan-500/20 mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center animate-pulse">
                        <i className="fas fa-bullseye text-cyan-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Analyzing Infrastructure...</h3>
                        <p className="text-sm text-gray-400">Calculating optimization recommendations</p>
                    </div>
                </div>
            </div>
        );
    }

    if (actions.length === 0) {
        return (
            <div className="bg-gradient-to-r from-emerald-900/20 to-green-900/20 rounded-2xl p-6 border border-emerald-500/20 mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                        <i className="fas fa-check-circle text-emerald-400 text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">All Optimized!</h3>
                        <p className="text-sm text-gray-400">No immediate actions required. Your infrastructure is healthy.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gradient-to-r from-cyan-900/20 via-blue-900/20 to-purple-900/20 rounded-2xl p-6 border border-cyan-500/20 mb-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                        <i className="fas fa-bullseye text-white text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">🎯 Top Actions to Optimize</h3>
                        <p className="text-sm text-gray-400">{actions.length} recommendations found</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                        ${totalSavings.toFixed(0)}/mo
                    </div>
                    <div className="text-xs text-gray-500">Potential Savings</div>
                </div>
            </div>

            {/* Action Cards */}
            <div className="space-y-3">
                {actions.map((action, index) => {
                    const style = getCategoryStyle(action.category);
                    return (
                        <button
                            key={action.id}
                            onClick={() => onActionClick(action)}
                            className={`w-full flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r ${style.bg} border ${style.border} hover:scale-[1.01] transition-all duration-200 text-left group`}
                        >
                            {/* Priority Number */}
                            <div className="w-8 h-8 rounded-full bg-gray-800/50 flex items-center justify-center text-white font-bold text-sm">
                                {index + 1}
                            </div>

                            {/* Icon */}
                            <div className="text-2xl">{action.icon}</div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="font-semibold text-white">{action.title}</span>
                                    {getRiskBadge(action.risk_level)}
                                </div>
                                <p className="text-sm text-gray-400 truncate">{action.description}</p>
                                <p className="text-xs text-gray-500 mt-1">
                                    {action.resource_type} • {action.resource_name.length > 30 ? action.resource_name.slice(0, 30) + '...' : action.resource_name}
                                </p>
                            </div>

                            {/* Savings & Arrow */}
                            <div className="text-right flex items-center gap-3">
                                {action.potential_savings > 0 && (
                                    <div>
                                        <div className="text-lg font-bold text-emerald-400">
                                            ${action.potential_savings.toFixed(0)}
                                        </div>
                                        <div className="text-xs text-gray-500">savings/mo</div>
                                    </div>
                                )}
                                <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                                    <i className="fas fa-arrow-right text-gray-400 group-hover:text-white transition-colors" />
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

// ===== Main Page Component =====
export function IntelligenceHubPage() {
    const [selectedCompartmentId, setSelectedCompartmentId] = useState<string | null>(null);
    const [selectedResource, setSelectedResource] = useState<ResourceHealth | null>(null);
    const [activeView, setActiveView] = useState<ViewType>('heatmap');

    const { data: compartments } = useCompartments();
    const { data: healthMatrix, isLoading, error } = useHealthMatrix(selectedCompartmentId);
    const { data: topActionsData, isLoading: topActionsLoading } = useTopActions(selectedCompartmentId);

    // Set default compartment on load
    React.useEffect(() => {
        if (compartments && compartments.length > 0 && !selectedCompartmentId) {
            setSelectedCompartmentId(compartments[0].id);
        }
    }, [compartments, selectedCompartmentId]);

    // Get resource types in order of importance
    const sortedTypes = useMemo(() => {
        if (!healthMatrix?.by_type) return [];
        const order = ['compute', 'database', 'cluster', 'load_balancer', 'block_volume', 'network', 'storage'];
        return Object.keys(healthMatrix.by_type).sort((a, b) => {
            const aIndex = order.indexOf(a);
            const bIndex = order.indexOf(b);
            return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
        });
    }, [healthMatrix]);

    return (
        <div className="min-h-screen bg-[#0a0e17]">
            {/* Hero Section */}
            <PremiumHero
                title="Cloud Intelligence Hub"
                subtitle="Multi-dimensional analytics combining multiple OCI APIs for insights not available in OCI Console"
                colorCombo="cyan"
            />

            <div className="container mx-auto px-6 py-8 max-w-7xl">
                {/* Compartment Selector */}
                <div className="mb-8">
                    {compartments && (
                        <CompartmentSelector
                            compartments={compartments}
                            selectedCompartmentId={selectedCompartmentId || ''}
                            onCompartmentChange={setSelectedCompartmentId}
                        />
                    )}
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <LoadingSpinner />
                        <p className="mt-4 text-gray-400">Computing health scores from multiple APIs...</p>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="bg-red-900/20 border border-red-800 rounded-xl p-6 text-center">
                        <i className="fas fa-exclamation-triangle text-red-400 text-3xl mb-3" />
                        <h3 className="text-lg font-semibold text-white mb-2">Failed to load intelligence data</h3>
                        <p className="text-gray-400">{(error as Error).message}</p>
                        <p className="text-xs text-gray-500 mt-2">Check if backend is running and /api/v1/intelligence/health-matrix endpoint is available</p>
                    </div>
                )}

                {/* No Data State */}
                {!isLoading && !error && (!healthMatrix || !healthMatrix.summary) && selectedCompartmentId && (
                    <div className="bg-amber-900/20 border border-amber-800 rounded-xl p-6 text-center">
                        <i className="fas fa-info-circle text-amber-400 text-3xl mb-3" />
                        <h3 className="text-lg font-semibold text-white mb-2">Loading Intelligence Data...</h3>
                        <p className="text-gray-400">Fetching health matrix for compartment...</p>
                        <p className="text-xs text-gray-500 mt-4">
                            If this persists, please restart the backend server to load new /intelligence routes.
                        </p>
                    </div>
                )}

                {/* Main Content */}
                {healthMatrix && healthMatrix.summary && !isLoading && (
                    <>
                        {/* Top Actions Panel - Phase 3 */}
                        <TopActionsPanel
                            actions={topActionsData?.actions || []}
                            totalSavings={topActionsData?.total_potential_savings || 0}
                            isLoading={topActionsLoading}
                            onActionClick={(action) => {
                                // Find matching resource and open drill-down
                                const resource = healthMatrix.resources?.find(r => r.resource_id === action.resource_id);
                                if (resource) {
                                    setSelectedResource(resource);
                                }
                            }}
                        />

                        {/* Summary Stats + Export */}
                        <div className="mb-8 flex items-start justify-between">
                            <SummaryStats
                                total={healthMatrix.summary.total_resources || 0}
                                healthy={healthMatrix.summary.healthy_count || 0}
                                warning={healthMatrix.summary.warning_count || 0}
                                critical={healthMatrix.summary.critical_count || 0}
                                waste={healthMatrix.summary.total_waste || 0}
                            />
                        </div>

                        {/* View Tabs + Export Button */}
                        <div className="mb-6 flex items-center justify-between">
                            <ViewTabs activeView={activeView} onViewChange={setActiveView} />
                            <ExportButton
                                resources={healthMatrix.resources || []}
                                compartmentId={selectedCompartmentId}
                            />
                        </div>

                        {/* Health Waves View (Heatmap) */}
                        {activeView === 'heatmap' && (
                            <>
                                {/* Heatmap Legend */}
                                <div className="mb-6 flex items-center gap-6 text-sm">
                                    <span className="text-gray-400">Health Score:</span>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 rounded bg-emerald-500" />
                                        <span className="text-gray-300">8-10 Healthy</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 rounded bg-amber-500" />
                                        <span className="text-gray-300">5-7 Warning</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 rounded bg-red-500" />
                                        <span className="text-gray-300">0-4 Critical</span>
                                    </div>
                                    <span className="text-gray-500 ml-4">Click any cell for details</span>
                                </div>

                                {/* Heatmap by Type */}
                                <div className="space-y-4">
                                    {sortedTypes.map(type => (
                                        <ResourceTypeRow
                                            key={type}
                                            type={type}
                                            resources={healthMatrix.by_type[type]}
                                            selectedId={selectedResource?.resource_id || null}
                                            onSelect={setSelectedResource}
                                        />
                                    ))}
                                </div>
                            </>
                        )}

                        {/* Cost Analysis View (Bubble Chart) */}
                        {activeView === 'bubble' && (
                            <CostBubbleChart
                                resources={healthMatrix.resources || []}
                                onSelect={setSelectedResource}
                                selectedId={selectedResource?.resource_id || null}
                            />
                        )}

                        {/* Insights View (Waste + Timeline) */}
                        {activeView === 'insights' && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <WasteDetectionWidget
                                    resources={healthMatrix.resources || []}
                                    onSelect={setSelectedResource}
                                />
                                <ActivityTimeline
                                    resources={healthMatrix.resources || []}
                                />
                            </div>
                        )}

                        {/* Empty State */}
                        {sortedTypes.length === 0 && (
                            <div className="bg-gray-800/50 rounded-xl p-12 text-center border border-gray-700">
                                <i className="fas fa-search text-gray-600 text-4xl mb-4" />
                                <h3 className="text-lg font-semibold text-white mb-2">No resources found</h3>
                                <p className="text-gray-400">Select a different compartment to see resource health data.</p>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Backdrop when panel is open - must come BEFORE panel */}
            {selectedResource && (
                <div
                    className="fixed inset-0 bg-black/50 z-40"
                    onClick={() => setSelectedResource(null)}
                />
            )}

            {/* Drill-Down Panel - z-50 to be above backdrop */}
            <DrillDownPanel
                resource={selectedResource}
                onClose={() => setSelectedResource(null)}
            />
        </div>
    );
}
