import React from 'react';

interface PremiumHeroProps {
    title: string;
    subtitle: string;
    stats?: { label: string; value: string; color?: string }[];
    pattern?: 'default' | 'waves' | 'circles';
    colorCombo?: 'blue' | 'emerald' | 'purple' | 'cyan' | 'orange' | 'red';
}

export const PremiumHero: React.FC<PremiumHeroProps> = ({
    title,
    subtitle,
    stats,
    pattern = 'default',
    colorCombo = 'blue'
}) => {

    const gradients = {
        blue: 'from-blue-900 via-indigo-900 to-purple-900',
        emerald: 'from-emerald-900 via-teal-900 to-cyan-900',
        purple: 'from-purple-900 via-indigo-900 to-blue-900',
        cyan: 'from-cyan-900 via-blue-900 to-indigo-900',
        orange: 'from-orange-900 via-amber-900 to-red-900',
        red: 'from-red-900 via-orange-900 to-amber-900'
    };

    const accents = {
        blue: 'bg-blue-500',
        emerald: 'bg-emerald-500',
        purple: 'bg-purple-500',
        cyan: 'bg-cyan-500',
        orange: 'bg-orange-500',
        red: 'bg-red-500'
    };

    return (
        <div className={`bg-gradient-to-r ${gradients[colorCombo]} rounded-3xl p-8 shadow-xl mb-8 text-white relative overflow-hidden transition-all duration-500`}>
            {/* Abstract Shapes */}
            <div className={`absolute top-0 right-0 w-96 h-96 ${accents[colorCombo]} rounded-full mix-blend-overlay filter blur-3xl opacity-20 -mr-20 -mt-20`}></div>
            <div className={`absolute bottom-0 left-0 w-64 h-64 ${accents[colorCombo]} rounded-full mix-blend-overlay filter blur-3xl opacity-20 -ml-10 -mb-10`}></div>

            {/* Content */}
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
                <div>
                    <div className="flex items-center space-x-2 mb-2 text-white/60 uppercase tracking-widest text-xs font-bold">
                        <i className="fas fa-layer-group"></i>
                        <span>GenAI CloudOps</span>
                    </div>
                    <h1 className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-200">
                        {title}
                    </h1>
                    <p className="text-white/70 mt-2 max-w-lg text-lg">
                        {subtitle}
                    </p>
                </div>

                {/* Optional Right-Side Stats */}
                {stats && stats.length > 0 && (
                    <div className="flex gap-4">
                        {stats.map((stat, idx) => (
                            <div key={idx} className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 min-w-[120px] text-center">
                                <div className="text-xs text-white/70 uppercase font-bold mb-1">{stat.label}</div>
                                <div className="text-2xl font-bold">{stat.value}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
