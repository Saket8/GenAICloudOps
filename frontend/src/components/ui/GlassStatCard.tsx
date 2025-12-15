import React from 'react';

interface GlassStatCardProps {
    title: string;
    value: string | number;
    subValue?: string;
    icon: string;
    color: string;
    trend?: 'up' | 'down' | 'neutral';
    onClick?: () => void;
}

export const GlassStatCard: React.FC<GlassStatCardProps> = ({ title, value, subValue, icon, color, trend, onClick }) => {
    const colorStyles = {
        emerald: 'from-emerald-500 to-emerald-600',
        blue: 'from-blue-500 to-blue-600',
        purple: 'from-purple-500 to-purple-600',
        orange: 'from-orange-500 to-orange-600',
        red: 'from-red-500 to-red-600',
        cyan: 'from-cyan-500 to-cyan-600',
        indigo: 'from-indigo-500 to-indigo-600',
        yellow: 'from-yellow-500 to-yellow-600' // Added yellow support
    }[color] || 'from-gray-500 to-gray-600';

    return (
        <div
            onClick={onClick}
            className={`bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all group ${onClick ? 'cursor-pointer' : ''}`}
        >
            <div className="flex justify-between items-start">
                <div>
                    <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{title}</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white group-hover:scale-105 transition-transform origin-left">
                        {value}
                    </div>
                    {subValue && <div className="text-xs font-medium text-gray-500 mt-1">{subValue}</div>}
                </div>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorStyles} flex items-center justify-center text-white shadow-lg`}>
                    <i className={`${icon} text-lg`}></i>
                </div>
            </div>
        </div>
    );
};
