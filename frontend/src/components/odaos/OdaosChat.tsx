/**
 * ODAOS Chat — SSE-streaming chat panel for Operational Insights.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { streamChat } from '../../api/odaosApi';
import { UsageFooter, UsageMetrics } from './UsageFooter';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    isStreaming?: boolean;
    chart?: any;
    usage?: UsageMetrics;
}

export default function OdaosChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const cancelRef = useRef<() => void>();

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height =
                Math.min(inputRef.current.scrollHeight, 160) + 'px';
        }
    }, [input]);

    const handleSubmit = useCallback(
        (e: React.FormEvent) => {
            e.preventDefault();
            const trimmed = input.trim();
            if (!trimmed || isStreaming) return;
            setInput('');

            // Add user and placeholder assistant messages
            setMessages((prev) => [
                ...prev,
                { role: 'user', content: trimmed },
                { role: 'assistant', content: '', isStreaming: true },
            ]);
            setIsStreaming(true);

            let fullContent = '';

            cancelRef.current = streamChat(
                trimmed,
                sessionId,
                // onToken
                (token) => {
                    fullContent += token;
                    setMessages((prev) => {
                        const clone = [...prev];
                        clone[clone.length - 1] = {
                            role: 'assistant',
                            content: fullContent,
                            isStreaming: true,
                        };
                        return clone;
                    });
                },
                // onChart
                (chart) => {
                    setMessages((prev) => {
                        const clone = [...prev];
                        clone[clone.length - 1] = {
                            ...clone[clone.length - 1],
                            chart,
                        };
                        return clone;
                    });
                },
                // onSuggestions
                () => { },
                // onUsage
                (data) => {
                    setMessages((prev) => {
                        const clone = [...prev];
                        clone[clone.length - 1] = {
                            ...clone[clone.length - 1],
                            usage: data,
                        };
                        return clone;
                    });
                },
                // onDone
                (sid) => {
                    setMessages((prev) => {
                        const clone = [...prev];
                        clone[clone.length - 1] = {
                            ...clone[clone.length - 1],
                            isStreaming: false,
                        };
                        return clone;
                    });
                    if (sid && !sessionId) setSessionId(sid);
                    setIsStreaming(false);
                },
                // onError
                (msg) => {
                    setMessages((prev) => {
                        const clone = [...prev];
                        clone[clone.length - 1] = {
                            role: 'assistant',
                            content: fullContent || `Error: ${msg}`,
                            isStreaming: false,
                        };
                        return clone;
                    });
                    setIsStreaming(false);
                },
            );
        },
        [input, isStreaming, sessionId],
    );

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleQuickReply = (q: string) => {
        setInput(q);
        inputRef.current?.focus();
    };

    const suggestions = [
        { label: 'Show me revenue trends', desc: 'Monthly revenue over time' },
        { label: 'Customer distribution by region', desc: 'Geographic breakdown' },
        { label: 'How is the database performing?', desc: 'Database health status' },
        { label: 'Show top SQL consumers', desc: 'Resource-heavy queries' },
    ];

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                            ODAOS AI Assistant
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
                            Ask questions about your Oracle BRM data and database operations
                        </p>
                        <div className="grid grid-cols-2 gap-3 max-w-xl w-full">
                            {suggestions.map((item, i) => (
                                <motion.button
                                    key={item.label}
                                    initial={{ opacity: 0, y: 12 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.05 * i, duration: 0.2 }}
                                    onClick={() => handleQuickReply(item.label)}
                                    className="text-left p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                                >
                                    <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                        {item.label}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                        {item.desc}
                                    </p>
                                </motion.button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto space-y-4">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                                        }`}
                                >
                                    {msg.role === 'assistant' ? (
                                        <>
                                            <div className="prose prose-sm dark:prose-invert max-w-none">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {msg.content || (msg.isStreaming ? '...' : '')}
                                                </ReactMarkdown>
                                                {msg.isStreaming && (
                                                    <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-0.5" />
                                                )}
                                            </div>
                                            {!msg.isStreaming && (
                                                <UsageFooter usage={msg.usage} />
                                            )}
                                        </>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        ))}
                        <div ref={bottomRef} />
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="px-4 pb-4 pt-2">
                <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
                    <div className="relative bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-2xl shadow-sm focus-within:border-blue-500 transition-colors">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your billing data or database..."
                            rows={1}
                            className="w-full bg-transparent outline-none resize-none px-4 pt-3 pb-10 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
                            style={{ minHeight: '48px', maxHeight: '160px' }}
                        />
                        <div className="absolute bottom-2 right-2">
                            <button
                                type="submit"
                                disabled={!input.trim() || isStreaming}
                                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${input.trim() && !isStreaming
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                {isStreaming ? (
                                    <Loader2 size={16} className="animate-spin" />
                                ) : (
                                    <ArrowUp size={16} />
                                )}
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-xs text-gray-400 mt-2">
                        ODAOS AI can make mistakes. Verify important information.
                    </p>
                </form>
            </div>
        </div>
    );
}
