import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface Layer {
    id: string;
    name: string;
    subtitle: string;
    route: string;
    icon: string;
    requiredPermissions?: string[];
    gradient: string;
    glowColor: string;
    accentColor: string;
}

const layers: Layer[] = [
    {
        id: 'infrastructure',
        name: 'Infrastructure',
        subtitle: 'Servers, networks & cloud resources',
        route: '/infrastructure/providers',
        icon: 'fas fa-server',
        requiredPermissions: ['can_view_dashboard', 'can_view_cost_analyzer', 'can_view_alerts'],
        gradient: 'from-blue-600 via-blue-500 to-cyan-400',
        glowColor: 'rgba(59, 130, 246, 0.4)',
        accentColor: '#3b82f6',
    },
    {
        id: 'application-ops',
        name: 'Application Ops',
        subtitle: 'Apps, containers & deployments',
        route: '/application/providers',
        icon: 'fas fa-cube',
        requiredPermissions: ['can_view_pod_analyzer'],
        gradient: 'from-purple-600 via-purple-500 to-pink-400',
        glowColor: 'rgba(168, 85, 247, 0.4)',
        accentColor: '#a855f7',
    },
    {
        id: 'business-ops',
        name: 'Business Ops',
        subtitle: 'Analytics, costs & BI',
        route: '/business/providers',
        icon: 'fas fa-chart-line',
        requiredPermissions: ['can_view_dashboard', 'can_view_cost_analyzer'],
        gradient: 'from-emerald-600 via-emerald-500 to-teal-400',
        glowColor: 'rgba(16, 185, 129, 0.4)',
        accentColor: '#10b981',
    },
    {
        id: 'security-ops',
        name: 'Security Ops',
        subtitle: 'Access, compliance & threats',
        route: '/security/providers',
        icon: 'fas fa-shield-halved',
        requiredPermissions: ['can_view_access_analyzer', 'can_approve_remediation', 'can_execute_remediation'],
        gradient: 'from-orange-600 via-orange-500 to-amber-400',
        glowColor: 'rgba(249, 115, 22, 0.4)',
        accentColor: '#f97316',
    },
    {
        id: 'administration',
        name: 'Administration',
        subtitle: 'Users, roles & config',
        route: '/administration',
        icon: 'fas fa-gear',
        requiredPermissions: ['can_manage_users', 'can_manage_roles'],
        gradient: 'from-slate-500 via-slate-400 to-zinc-400',
        glowColor: 'rgba(100, 116, 139, 0.4)',
        accentColor: '#64748b',
    },
];

// Compact 3D Card Component
const LayerCard: React.FC<{
    layer: Layer;
    index: number;
    onClick: () => void;
}> = ({ layer, index, onClick }) => {
    const [mousePosition, setMousePosition] = useState({ x: 0.5, y: 0.5 });
    const [isHovered, setIsHovered] = useState(false);

    const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setMousePosition({
            x: (e.clientX - rect.left) / rect.width,
            y: (e.clientY - rect.top) / rect.height,
        });
    };

    const rotateX = isHovered ? (mousePosition.y - 0.5) * -15 : 0;
    const rotateY = isHovered ? (mousePosition.x - 0.5) * 15 : 0;

    return (
        <button
            onClick={onClick}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => { setIsHovered(false); setMousePosition({ x: 0.5, y: 0.5 }); }}
            className="group relative w-full focus:outline-none"
            style={{ perspective: '1000px' }}
        >
            <div
                className="relative rounded-2xl overflow-hidden transition-all duration-300 ease-out"
                style={{
                    transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) ${isHovered ? 'translateZ(15px) scale(1.03)' : 'translateZ(0) scale(1)'}`,
                    transformStyle: 'preserve-3d',
                    boxShadow: isHovered
                        ? `0 20px 40px -15px ${layer.glowColor}, 0 0 50px ${layer.glowColor}`
                        : '0 8px 30px -10px rgba(0,0,0,0.4)',
                }}
            >
                {/* Gradient Background */}
                <div className={`absolute inset-0 bg-gradient-to-br ${layer.gradient} opacity-95`} />

                {/* Glass Overlay */}
                <div className="absolute inset-0 bg-gradient-to-b from-white/25 via-white/5 to-black/10" />

                {/* Animated Border Glow */}
                <div
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{
                        boxShadow: `inset 0 0 30px ${layer.glowColor}`,
                    }}
                />

                {/* Content - Compact Layout */}
                <div className="relative p-5 flex items-center gap-4 min-h-[100px]">

                    {/* Icon Container - Smaller */}
                    <div
                        className="flex-shrink-0 w-14 h-14 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 transition-all duration-300 group-hover:scale-110 group-hover:bg-white/30"
                        style={{
                            boxShadow: isHovered ? `0 0 25px ${layer.glowColor}` : 'none',
                        }}
                    >
                        <i className={`${layer.icon} text-2xl text-white drop-shadow-lg`} />
                    </div>

                    {/* Text Content */}
                    <div className="flex-1 text-left min-w-0">
                        <h3 className="text-lg font-bold text-white mb-0.5 truncate drop-shadow-md">
                            {layer.name}
                        </h3>
                        <p className="text-sm text-white/75 truncate">
                            {layer.subtitle}
                        </p>
                    </div>

                    {/* Arrow */}
                    <div
                        className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center transition-all duration-300 group-hover:bg-white/20 group-hover:translate-x-1"
                    >
                        <i className="fas fa-chevron-right text-white text-sm" />
                    </div>
                </div>

                {/* Shine Sweep */}
                <div
                    className="absolute inset-0 pointer-events-none overflow-hidden"
                    style={{ opacity: isHovered ? 1 : 0 }}
                >
                    <div
                        className="absolute w-[200%] h-[200%] -translate-x-1/2 -translate-y-1/2"
                        style={{
                            background: 'linear-gradient(110deg, transparent 45%, rgba(255,255,255,0.15) 50%, transparent 55%)',
                            transform: `translate(${mousePosition.x * 100}%, ${mousePosition.y * 100}%)`,
                            transition: 'transform 0.1s',
                        }}
                    />
                </div>
            </div>
        </button>
    );
};

export function LayersSelectionPage() {
    const navigate = useNavigate();
    const { logout, user, permissions } = useAuth();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const hasPermission = (requiredPermissions?: string[]): boolean => {
        if (!requiredPermissions || requiredPermissions.length === 0) {
            return true;
        }
        if (!permissions) {
            return false;
        }
        const permissionMap: Record<string, boolean> = {
            'can_view_dashboard': permissions.can_view_dashboard,
            'can_view_alerts': permissions.can_view_alerts,
            'can_approve_remediation': permissions.can_approve_remediation,
            'can_execute_remediation': permissions.can_execute_remediation,
            'can_manage_users': permissions.can_manage_users,
            'can_manage_roles': permissions.can_manage_roles,
            'can_view_access_analyzer': permissions.can_view_access_analyzer,
            'can_view_pod_analyzer': permissions.can_view_pod_analyzer,
            'can_view_cost_analyzer': permissions.can_view_cost_analyzer,
            'can_use_chatbot': permissions.can_use_chatbot,
        };
        return requiredPermissions.some(permission => permissionMap[permission] === true);
    };

    const visibleLayers = layers.filter(layer => hasPermission(layer.requiredPermissions));

    return (
        <div className="min-h-screen bg-[#0a0e17] relative overflow-hidden">

            {/* Animated Background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {/* Floating Orbs */}
                <div
                    className="absolute w-[600px] h-[600px] rounded-full blur-[120px] animate-float-slow"
                    style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.25) 0%, transparent 70%)', top: '-15%', left: '-5%' }}
                />
                <div
                    className="absolute w-[700px] h-[700px] rounded-full blur-[130px] animate-float-slow-reverse"
                    style={{ background: 'radial-gradient(circle, rgba(168,85,247,0.2) 0%, transparent 70%)', bottom: '-20%', right: '-10%' }}
                />
                <div
                    className="absolute w-[400px] h-[400px] rounded-full blur-[100px] animate-pulse"
                    style={{ background: 'radial-gradient(circle, rgba(16,185,129,0.15) 0%, transparent 70%)', top: '40%', left: '40%' }}
                />

                {/* Grid Pattern */}
                <div
                    className="absolute inset-0 opacity-[0.04]"
                    style={{
                        backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
                        backgroundSize: '50px 50px'
                    }}
                />

                {/* Vignette */}
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#0a0e17]/80" />
            </div>

            <div className="container mx-auto px-6 py-8 relative z-10 max-w-6xl">

                {/* Header - Compact */}
                <div className={`flex items-center justify-between mb-10 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-5'}`}>
                    <div>
                        {/* Status Badge */}
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.06] border border-white/10 backdrop-blur-sm mb-4">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            <span className="text-xs font-medium text-gray-400">All Systems Online</span>
                        </div>

                        <h1 className="text-4xl font-bold text-white mb-2">
                            Cloud Command Centre
                        </h1>
                        <p className="text-gray-400">
                            Select an operational layer to continue
                        </p>
                    </div>

                    {/* User Card - Compact */}
                    <div className="flex items-center gap-3 bg-white/[0.05] backdrop-blur-xl border border-white/10 rounded-xl px-4 py-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="min-w-0">
                            <p className="font-medium text-white text-sm truncate max-w-[150px]">{user?.username}</p>
                            <p className="text-xs text-gray-400 truncate max-w-[150px]">{user?.email}</p>
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    await logout();
                                    navigate('/login');
                                } catch (error) {
                                    console.error('Logout error:', error);
                                }
                            }}
                            className="ml-2 p-2.5 rounded-lg bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-500/50 text-gray-400 hover:text-red-400 transition-all duration-300"
                            title="Sign Out"
                        >
                            <i className="fas fa-sign-out-alt" />
                        </button>
                    </div>
                </div>

                {/* Layers Grid - 3 columns, compact */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {visibleLayers.map((layer, index) => (
                        <div
                            key={layer.id}
                            className={`transition-all duration-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
                            style={{ transitionDelay: `${200 + index * 100}ms` }}
                        >
                            <LayerCard
                                layer={layer}
                                index={index}
                                onClick={() => navigate(layer.route)}
                            />
                        </div>
                    ))}
                </div>

                {/* Premium Footer with Gradient Wave */}
                <div
                    className={`mt-20 relative transition-all duration-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}
                    style={{ transitionDelay: '600ms' }}
                >
                    {/* Animated Gradient Wave SVG */}
                    <div className="absolute inset-x-0 -top-24 h-32 overflow-hidden pointer-events-none">
                        <svg
                            viewBox="0 0 1440 120"
                            className="w-full h-full"
                            preserveAspectRatio="none"
                        >
                            <defs>
                                <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#f97316" />
                                    <stop offset="25%" stopColor="#eab308" />
                                    <stop offset="50%" stopColor="#22c55e" />
                                    <stop offset="75%" stopColor="#06b6d4" />
                                    <stop offset="100%" stopColor="#a855f7" />
                                </linearGradient>
                                <linearGradient id="waveGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#ec4899" />
                                    <stop offset="50%" stopColor="#8b5cf6" />
                                    <stop offset="100%" stopColor="#3b82f6" />
                                </linearGradient>
                            </defs>
                            {/* Wave 1 */}
                            <path
                                className="animate-wave-slow"
                                fill="none"
                                stroke="url(#waveGradient)"
                                strokeWidth="3"
                                d="M0,60 C200,100 400,20 600,60 C800,100 1000,20 1200,60 C1300,80 1400,40 1440,60"
                                opacity="0.8"
                            />
                            {/* Wave 2 */}
                            <path
                                className="animate-wave-slow-reverse"
                                fill="none"
                                stroke="url(#waveGradient2)"
                                strokeWidth="2"
                                d="M0,50 C240,90 480,10 720,50 C960,90 1200,10 1440,50"
                                opacity="0.6"
                            />
                            {/* Wave 3 */}
                            <path
                                className="animate-wave-slower"
                                fill="none"
                                stroke="url(#waveGradient)"
                                strokeWidth="1.5"
                                d="M0,70 C180,30 360,110 540,70 C720,30 900,110 1080,70 C1260,30 1440,70 1440,70"
                                opacity="0.4"
                            />
                        </svg>
                    </div>

                    {/* Footer Content */}
                    <div className="relative pt-8 pb-6">
                        <div className="text-center mb-6">
                            <p className="text-gray-400 text-sm font-light tracking-wide">
                                Copyright © 2025, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-medium">CloudOps Team</span> and/or its affiliates.
                            </p>
                        </div>
                        <div className="flex flex-wrap justify-center items-center gap-3 text-xs">
                            <a href="#" className="px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-cyan-400 transition-all duration-300 border border-white/5 hover:border-cyan-500/30">
                                About CloudOps
                            </a>
                            <a href="#" className="px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-emerald-400 transition-all duration-300 border border-white/5 hover:border-emerald-500/30">
                                Contact Us
                            </a>
                            <a href="#" className="px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-amber-400 transition-all duration-300 border border-white/5 hover:border-amber-500/30">
                                Legal Notices
                            </a>
                            <a href="#" className="px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-purple-400 transition-all duration-300 border border-white/5 hover:border-purple-500/30">
                                Terms of Use & Privacy
                            </a>
                            <a href="#" className="px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-pink-400 transition-all duration-300 border border-white/5 hover:border-pink-500/30">
                                Document Conventions
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            {/* CSS Animations */}
            <style>{`
                @keyframes float-slow {
                    0%, 100% { transform: translate(0, 0); }
                    50% { transform: translate(30px, -20px); }
                }
                @keyframes float-slow-reverse {
                    0%, 100% { transform: translate(0, 0); }
                    50% { transform: translate(-30px, 20px); }
                }
                @keyframes wave-flow {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50px); }
                }
                @keyframes wave-flow-reverse {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(50px); }
                }
                .animate-float-slow {
                    animation: float-slow 15s ease-in-out infinite;
                }
                .animate-float-slow-reverse {
                    animation: float-slow-reverse 18s ease-in-out infinite;
                }
                .animate-wave-slow {
                    animation: wave-flow 8s ease-in-out infinite alternate;
                }
                .animate-wave-slow-reverse {
                    animation: wave-flow-reverse 10s ease-in-out infinite alternate;
                }
                .animate-wave-slower {
                    animation: wave-flow 12s ease-in-out infinite alternate;
                }
            `}</style>
        </div>
    );
}
