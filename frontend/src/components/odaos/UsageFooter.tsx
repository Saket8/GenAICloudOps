import React from 'react';
import { Zap, Leaf, ArrowRight, ArrowLeft, Coins } from 'lucide-react';

export interface UsageMetrics {
    input_tokens: number | null;
    output_tokens: number | null;
    total_tokens: number | null;
    energy_wh: number | null;
    co2_g: number | null;
    response_time_ms?: number | null;
}

interface UsageFooterProps {
    usage?: UsageMetrics;
}

export function UsageFooter({ usage }: UsageFooterProps) {
    const inputTokens = usage?.input_tokens;
    const outputTokens = usage?.output_tokens;
    const totalTokens = usage?.total_tokens;
    const energyWh = usage?.energy_wh;
    const co2g = usage?.co2_g;
    const responseTimeMs = usage?.response_time_ms;

    const tokenText = (value?: number) =>
        typeof value === 'number' ? value.toLocaleString() : 'Not Available';
    const numberText = (value?: number, unit?: string) =>
        typeof value === 'number' ? `${value.toFixed(4)} ${unit}` : 'Not Available';
    const responseTimeText = (value?: number) => {
        if (typeof value !== 'number') return 'Not Available';
        if (value < 1000) return `${value} ms`;
        return `${(value / 1000).toFixed(2)} s`;
    };

    return (
        <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700/60">
            <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-1 font-medium">
                AI Usage Summary
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-gray-500 dark:text-gray-400 font-medium overflow-x-auto whitespace-nowrap">
            <span className="flex items-center gap-1" title="Input tokens received">
                <ArrowRight size={12} className="text-gray-400 shrink-0" />
                Input Tokens: {tokenText(inputTokens ?? undefined)}
            </span>
            <span className="flex items-center gap-1" title="Output tokens generated">
                <ArrowLeft size={12} className="text-gray-400 shrink-0" />
                Output Tokens: {tokenText(outputTokens ?? undefined)}
            </span>
            <span className="flex items-center gap-1" title="Total tokens processed">
                <Coins size={12} className="text-gray-400 shrink-0" />
                Total Tokens: {tokenText(totalTokens ?? undefined)}
            </span>
            <span className="flex items-center gap-1" title="Estimated power used for this answer">
                <Zap size={12} className="text-yellow-500 shrink-0" />
                Estimated Energy Usage: {numberText(energyWh ?? undefined, 'Wh')}
            </span>
            <span className="flex items-center gap-1" title="Estimated carbon emissions for this answer">
                <Leaf size={12} className="text-emerald-500 shrink-0" />
                Estimated CO2 Emissions: {numberText(co2g ?? undefined, 'g')}
            </span>
            <span className="flex items-center gap-1" title="How long the AI took to respond">
                Response Time: {responseTimeText(responseTimeMs ?? undefined)}
            </span>
            </div>
        </div>
    );
}
