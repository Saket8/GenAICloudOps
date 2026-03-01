/**
 * ODAOS Prompt Library — Filterable prompt card grid with categories,
 * favorites, history, search, and difficulty pills.
 */
import React, { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Star, History, RefreshCw, X, Loader2, ChevronLeft, Play, Check, Copy } from 'lucide-react';
import {
    listPrompts,
    listCategories,
    getFavorites,
    getPromptHistory,
    getPrompt,
    toggleFavorite,
    streamPromptExecution,
} from '../../api/odaosApi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { UsageFooter, UsageMetrics } from './UsageFooter';

const SmartChart = lazy(() => import('./SmartChart'));

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface PromptSummary {
    id: string;
    title: string;
    description: string;
    category: string;
    difficulty: string;
    tags: string[];
    is_favorite?: boolean;
}

interface PromptCategory {
    id: string;
    name: string;
    display_name: string;
    prompt_count: number;
}

interface HistoryEntry {
    id: string;
    prompt_id: string;
    prompt_title: string;
    status: string;
    execution_time_ms: number;
    executed_at: string;
}

/* ------------------------------------------------------------------ */
/* Sub-Components                                                      */
/* ------------------------------------------------------------------ */

function PromptCard({
    prompt,
    onSelect,
}: {
    prompt: PromptSummary;
    onSelect: (id: string) => void;
}) {
    const difficultyColors: Record<string, string> = {
        beginner: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        intermediate: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        advanced: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    };

    return (
        <button
            onClick={() => onSelect(prompt.id)}
            className="text-left w-full p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md transition-all group"
        >
            <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 line-clamp-2">
                    {prompt.title}
                </h3>
                {prompt.is_favorite && (
                    <Star size={14} className="text-yellow-500 fill-yellow-500 flex-shrink-0 ml-2" />
                )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
                {prompt.description}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${difficultyColors[prompt.difficulty] || 'bg-gray-100 text-gray-600'}`}>
                    {prompt.difficulty}
                </span>
                {prompt.tags?.slice(0, 2).map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {tag}
                    </span>
                ))}
            </div>
        </button>
    );
}

/* ------------------------------------------------------------------ */
/* Prompt Detail Modal                                                 */
/* ------------------------------------------------------------------ */

function PromptDetailModal({
    promptId,
    onClose,
}: {
    promptId: string;
    onClose: () => void;
}) {
    const queryClient = useQueryClient();
    const { data: prompt, isLoading } = useQuery({
        queryKey: ['odaos-prompt', promptId],
        queryFn: () => getPrompt(promptId),
    });

    const [executing, setExecuting] = useState(false);
    const [output, setOutput] = useState('');
    const [executionChartData, setExecutionChartData] = useState<any | null>(null);
    const [usageMetrics, setUsageMetrics] = useState<UsageMetrics | null>(null);
    const [params, setParams] = useState<Record<string, any>>({});
    const [copied, setCopied] = useState(false);
    const [editedQuery, setEditedQuery] = useState('');

    useEffect(() => {
        if (prompt && prompt.parameters) {
            const defaults: Record<string, any> = { ...(prompt.default_values || {}) };
            prompt.parameters.forEach((p: any) => {
                if (p.default !== undefined && !(p.name in defaults)) {
                    defaults[p.name] = p.default;
                }
            });
            setParams(defaults);
        }
    }, [prompt]);

    // Compute template preview and sync editedQuery when params change
    let preview = prompt?.prompt_template || '';
    for (const [key, value] of Object.entries(params)) {
        preview = preview.replace(`{${key}}`, String(value));
    }

    useEffect(() => {
        setEditedQuery(preview);
    }, [preview]);

    const isQueryEdited = editedQuery !== preview;

    const handleExecute = () => {
        setExecuting(true);
        setOutput('');
        setExecutionChartData(null);
        setUsageMetrics(null);

        const customQuery = editedQuery !== preview ? editedQuery : undefined;

        let trace = '';
        streamPromptExecution(
            promptId,
            params,
            customQuery,
            (token) => { setOutput((prev) => prev + token); trace += ' [T] '; },
            (chart) => { setExecutionChartData(chart); trace += ' [C] '; },
            (data) => {
                setUsageMetrics(data);
                trace += ` [U: ${JSON.stringify(data)}] `;
                console.log("SETTING USAGE METRICS WITH:", data);
            },
            () => {
                setExecuting(false);
                // Refresh history
                queryClient.invalidateQueries({ queryKey: ['odaos-history'] });
            },
            (err) => {
                setOutput((prev) => prev + `\n\nError: ${err}`);
                setExecuting(false);
            }
        );
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(editedQuery);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleToggleFavorite = async () => {
        if (!prompt) return;
        try {
            const res = await toggleFavorite(prompt.id);
            // Update local cache
            queryClient.setQueryData(['odaos-prompt', prompt.id], (old: any) => ({ ...old, is_favorited: res.favorited }));
            queryClient.invalidateQueries({ queryKey: ['odaos-prompts'] });
            queryClient.invalidateQueries({ queryKey: ['odaos-favorites'] });
        } catch (e) {
            console.error(e);
        }
    };

    const renderInput = (param: any) => {
        const value = params[param.name] ?? param.default ?? '';
        const baseClass = "w-full mt-1 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 transition-colors";

        if (param.type === 'enum' && param.enum_values) {
            return (
                <select
                    value={value}
                    onChange={(e) => setParams({ ...params, [param.name]: e.target.value })}
                    className={baseClass}
                >
                    {param.enum_values.map((v: string) => (
                        <option key={v} value={v}>{v}</option>
                    ))}
                </select>
            );
        }

        if (param.type === 'integer' || param.type === 'number') {
            return (
                <input
                    type="number"
                    value={value}
                    onChange={(e) => setParams({ ...params, [param.name]: Number(e.target.value) })}
                    className={baseClass}
                />
            );
        }

        return (
            <input
                type="text"
                value={value}
                onChange={(e) => setParams({ ...params, [param.name]: e.target.value })}
                placeholder={param.description || param.name}
                className={baseClass}
            />
        );
    };

    if (isLoading) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-500 mx-auto" />
                </div>
            </div>
        );
    }

    if (!prompt) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
            <div
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-4xl max-h-[95vh] flex flex-col overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="px-6 pt-5 pb-3 border-b border-gray-200 dark:border-gray-700 flex items-start justify-between">
                    <div className="flex-1 min-w-0 pr-4">
                        <div className="flex items-center gap-2 mb-1.5 text-xs text-gray-500 dark:text-gray-400">
                            <span className={
                                prompt.difficulty_level === 'beginner' ? 'text-green-500' :
                                    prompt.difficulty_level === 'intermediate' ? 'text-yellow-500' :
                                        'text-red-500'
                            }>
                                {prompt.difficulty_level ? prompt.difficulty_level.charAt(0).toUpperCase() + prompt.difficulty_level.slice(1) : ''}
                            </span>
                            <span className="opacity-40">·</span>
                            <span>{prompt.estimated_runtime}</span>
                            {prompt.requires_approval && (
                                <>
                                    <span className="opacity-40">·</span>
                                    <span className="text-yellow-500">Needs Approval</span>
                                </>
                            )}
                        </div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white leading-snug">{prompt.title}</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1.5 leading-relaxed">{prompt.description}</p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                        <button
                            onClick={handleToggleFavorite}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                            <Star
                                size={18}
                                className={prompt.is_favorited ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'}
                            />
                        </button>
                        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                            <X size={18} className="text-gray-400" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
                    {/* Parameters */}
                    {prompt.parameters && prompt.parameters.length > 0 && (
                        <div>
                            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Parameters</h3>
                            <div className="space-y-3">
                                {prompt.parameters.map((param: any) => (
                                    <div key={param.name}>
                                        <label className="flex items-baseline gap-1.5 text-xs text-gray-500 dark:text-gray-400 mb-1">
                                            <span className="text-gray-700 dark:text-gray-300 font-medium">{param.name}</span>
                                            {param.required && <span className="text-red-500 text-[10px]">required</span>}
                                        </label>
                                        {renderInput(param)}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Preview */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Query preview</h3>
                                {isQueryEdited && (
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-500 font-medium">edited</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                {isQueryEdited && (
                                    <button
                                        onClick={() => setEditedQuery(preview)}
                                        className="flex items-center gap-1 text-[11px] text-yellow-500 hover:text-yellow-600"
                                    >
                                        Reset
                                    </button>
                                )}
                                <button
                                    onClick={handleCopy}
                                    className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                                >
                                    {copied ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                                    {copied ? 'Copied' : 'Copy'}
                                </button>
                            </div>
                        </div>
                        <textarea
                            value={editedQuery}
                            onChange={(e) => setEditedQuery(e.target.value)}
                            rows={6}
                            className="w-full p-4 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300 font-mono focus:outline-none focus:border-blue-500 transition-colors resize-y"
                        />
                    </div>

                    {/* Expected output hint */}
                    {prompt.expected_output && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                            <span className="font-semibold text-gray-700 dark:text-gray-300">Expected: </span>
                            {prompt.expected_output}
                        </p>
                    )}

                    {/* Chart visualization */}
                    {executionChartData && (
                        <Suspense fallback={
                            <div className="h-48 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
                                Loading visualization...
                            </div>
                        }>
                            <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden mt-4">
                                <SmartChart
                                    id={executionChartData.id || 'prompt-chart'}
                                    type={executionChartData.chart?.chart_type || executionChartData.type || executionChartData.chart_type || 'bar'}
                                    title={executionChartData.chart?.title || executionChartData.title || prompt.title}
                                    data={executionChartData.chart?.data || executionChartData.data || []}
                                    layout={executionChartData.chart?.layout || executionChartData.layout}
                                    narrative={executionChartData.narrative}
                                    drillDownOptions={executionChartData.drill_down_options || executionChartData.drillDownOptions}
                                />
                            </div>
                        </Suspense>
                    )}

                    {/* Execution output */}
                    {(output || executing) && (
                        <div className="mt-4">
                            <div className="flex items-center gap-2 mb-2">
                                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Output</h3>
                                {executing && <Loader2 size={12} className="animate-spin text-blue-500" />}
                            </div>
                            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 max-h-[400px] overflow-y-auto w-full max-w-full">
                                <div className="prose prose-sm dark:prose-invert max-w-none break-words text-gray-700 dark:text-gray-300">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{output || '...'}</ReactMarkdown>
                                </div>
                                {!executing && (
                                    <UsageFooter usage={usageMetrics || undefined} />
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3 bg-gray-50 dark:bg-gray-800/50">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors bg-white dark:bg-gray-800"
                    >
                        Close
                    </button>
                    <button
                        onClick={handleExecute}
                        disabled={executing}
                        className="px-5 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium"
                    >
                        {executing ? (
                            <Loader2 size={15} className="animate-spin" />
                        ) : (
                            <Play size={15} />
                        )}
                        {executing ? 'Running...' : 'Execute'}
                    </button>
                </div>
            </div>
        </div>
    );
}

/* ------------------------------------------------------------------ */
/* Debounce
/* ------------------------------------------------------------------ */

function useDebouncedValue(value: string, ms: number) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const t = setTimeout(() => setDebounced(value), ms);
        return () => clearTimeout(t);
    }, [value, ms]);
    return debounced;
}

/* ------------------------------------------------------------------ */
/* Main Component                                                      */
/* ------------------------------------------------------------------ */

export default function OdaosPromptLibrary({ onBack }: { onBack?: () => void }) {
    const queryClient = useQueryClient();

    const [searchInput, setSearchInput] = useState('');
    const debouncedSearch = useDebouncedValue(searchInput, 300);
    const [activeCategory, setActiveCategory] = useState<string | null>(null);
    const [activeDifficulty, setActiveDifficulty] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'all' | 'favorites' | 'history'>('all');
    const [page, setPage] = useState(1);
    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);

    // Queries
    const { data: promptsData, isLoading } = useQuery({
        queryKey: ['odaos-prompts', { search: debouncedSearch, category: activeCategory, difficulty: activeDifficulty, page }],
        queryFn: () =>
            listPrompts({
                search: debouncedSearch || undefined,
                category: activeCategory || undefined,
                difficulty: activeDifficulty || undefined,
                page,
                per_page: 18,
            }),
    });

    const { data: categories = [] } = useQuery({
        queryKey: ['odaos-categories'],
        queryFn: listCategories,
    });

    const { data: favorites = [] } = useQuery({
        queryKey: ['odaos-favorites'],
        queryFn: getFavorites,
    });

    const { data: historyData } = useQuery({
        queryKey: ['odaos-history'],
        queryFn: () => getPromptHistory(20, 0),
    });

    const history: HistoryEntry[] = historyData?.items || historyData || [];

    const prompts: PromptSummary[] = promptsData?.prompts || [];
    const total = promptsData?.total || 0;
    const perPage = 18;
    const totalPages = Math.ceil(total / perPage);

    const brmCategories = (categories as PromptCategory[]).filter((c) => c.name.startsWith('BRM_'));
    const dbaCategories = (categories as PromptCategory[]).filter((c) => c.name.startsWith('DBA_'));

    const resetFilters = () => {
        setSearchInput('');
        setActiveCategory(null);
        setActiveDifficulty(null);
        setPage(1);
    };

    const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

    return (
        <div className="flex h-full bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Left Sidebar */}
            <div className="w-48 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex flex-col">
                {onBack && (
                    <div className="p-3">
                        <button
                            onClick={onBack}
                            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
                        >
                            <ChevronLeft size={14} /> Back to Chat
                        </button>
                    </div>
                )}

                <div className="px-2 space-y-0.5">
                    <button
                        onClick={() => { setActiveTab('all'); setActiveCategory(null); }}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'all' && !activeCategory
                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium shadow-sm'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-700'
                            }`}
                    >
                        All Prompts
                        <span className="text-xs text-gray-400 tabular-nums">{total}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('favorites')}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'favorites'
                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium shadow-sm'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-700'
                            }`}
                    >
                        <span className="flex items-center gap-2"><Star size={13} /> Favorites</span>
                        <span className="text-xs text-gray-400 tabular-nums">{favorites.length}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('history')}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'history'
                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium shadow-sm'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-700'
                            }`}
                    >
                        <span className="flex items-center gap-2"><History size={13} /> History</span>
                        <span className="text-xs text-gray-400 tabular-nums">{history.length}</span>
                    </button>
                </div>

                {/* Categories */}
                {activeTab === 'all' && (categories as PromptCategory[]).length > 0 && (
                    <div className="flex-1 overflow-y-auto mt-3 px-2 border-t border-gray-200 dark:border-gray-700 pt-3">
                        {brmCategories.length > 0 && (
                            <>
                                <div className="px-3 pb-1.5 text-[10px] font-medium uppercase tracking-wider text-gray-400">
                                    BRM Analytics
                                </div>
                                {brmCategories.map((cat) => (
                                    <button
                                        key={cat.id}
                                        onClick={() => { setActiveTab('all'); setActiveCategory(cat.name); setPage(1); }}
                                        className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs transition-colors ${activeCategory === cat.name
                                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium'
                                            : 'text-gray-500 hover:bg-white dark:hover:bg-gray-700'
                                            }`}
                                    >
                                        <span className="truncate">{cat.display_name}</span>
                                        <span className="text-[10px] text-gray-400 tabular-nums">{cat.prompt_count}</span>
                                    </button>
                                ))}
                            </>
                        )}
                        {dbaCategories.length > 0 && (
                            <>
                                <div className="px-3 pt-3 pb-1.5 text-[10px] font-medium uppercase tracking-wider text-gray-400">DBA</div>
                                {dbaCategories.map((cat) => (
                                    <button
                                        key={cat.id}
                                        onClick={() => { setActiveTab('all'); setActiveCategory(cat.name); setPage(1); }}
                                        className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs transition-colors ${activeCategory === cat.name
                                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium'
                                            : 'text-gray-500 hover:bg-white dark:hover:bg-gray-700'
                                            }`}
                                    >
                                        <span className="truncate">{cat.display_name}</span>
                                        <span className="text-[10px] text-gray-400 tabular-nums">{cat.prompt_count}</span>
                                    </button>
                                ))}
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Toolbar */}
                <div className="px-5 py-2.5 border-b border-gray-200 dark:border-gray-700 flex items-center gap-3">
                    <div className="relative flex-1 max-w-sm">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => { setSearchInput(e.target.value); setPage(1); }}
                            placeholder="Search prompts..."
                            className="w-full pl-9 pr-8 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
                        />
                        {searchInput && (
                            <button onClick={() => setSearchInput('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400">
                                <X size={12} />
                            </button>
                        )}
                    </div>

                    {/* Difficulty pills */}
                    <div className="flex items-center gap-px bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
                        {(['beginner', 'intermediate', 'advanced'] as const).map((d) => (
                            <button
                                key={d}
                                onClick={() => { setActiveDifficulty(activeDifficulty === d ? null : d); setPage(1); }}
                                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${activeDifficulty === d
                                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                                    : 'text-gray-400 hover:text-gray-600'
                                    }`}
                            >
                                {capitalize(d)}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-1 ml-auto">
                        {(activeCategory || debouncedSearch || activeDifficulty) && (
                            <button onClick={resetFilters} className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600">
                                Clear filters
                            </button>
                        )}
                        <button
                            onClick={() => queryClient.invalidateQueries({ queryKey: ['odaos-prompts'] })}
                            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400"
                        >
                            <RefreshCw size={14} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5">
                    {activeTab === 'all' && (
                        isLoading ? (
                            <div className="flex items-center justify-center h-48">
                                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                            </div>
                        ) : prompts.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                                <p className="text-sm">No prompts match your filters</p>
                                <button onClick={resetFilters} className="mt-2 text-xs hover:underline">Clear filters</button>
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                    {prompts.map((p) => (
                                        <PromptCard
                                            key={p.id}
                                            prompt={p}
                                            onSelect={setSelectedPromptId}
                                        />
                                    ))}
                                </div>
                                {totalPages > 1 && (
                                    <div className="flex items-center justify-center gap-3 mt-6 text-xs text-gray-400">
                                        <button onClick={() => setPage(page - 1)} disabled={page <= 1} className="hover:text-gray-600 disabled:opacity-30">Previous</button>
                                        <span className="tabular-nums">{page} / {totalPages}</span>
                                        <button onClick={() => setPage(page + 1)} disabled={page >= totalPages} className="hover:text-gray-600 disabled:opacity-30">Next</button>
                                    </div>
                                )}
                            </>
                        )
                    )}

                    {activeTab === 'favorites' && (
                        <div>
                            <h2 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Favorites</h2>
                            {(favorites as PromptSummary[]).length === 0 ? (
                                <p className="text-sm text-gray-400 py-12 text-center">Star prompts to save them here</p>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                    {(favorites as PromptSummary[]).map((p) => (
                                        <PromptCard key={p.id} prompt={p} onSelect={setSelectedPromptId} />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div>
                            <h2 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Run History</h2>
                            {history.length === 0 ? (
                                <p className="text-sm text-gray-400 py-12 text-center">Execute a prompt to see it here</p>
                            ) : (
                                <div className="space-y-1">
                                    {history.map((entry) => (
                                        <div
                                            key={entry.id}
                                            onClick={() => setSelectedPromptId(entry.prompt_id)}
                                            className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                                        >
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-gray-900 dark:text-white truncate">{entry.prompt_title}</p>
                                            </div>
                                            <span className={`text-xs ${entry.status === 'success' ? 'text-emerald-500' : 'text-rose-500'}`}>
                                                {capitalize(entry.status)}
                                            </span>
                                            <span className="text-xs text-gray-400 tabular-nums">{entry.execution_time_ms}ms</span>
                                            <span className="text-xs text-gray-400">
                                                {new Date(entry.executed_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Detail Modal */}
            {selectedPromptId && (
                <PromptDetailModal
                    promptId={selectedPromptId}
                    onClose={() => setSelectedPromptId(null)}
                />
            )}
        </div>
    );
}
