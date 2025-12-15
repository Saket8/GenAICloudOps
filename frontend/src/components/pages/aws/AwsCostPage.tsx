import React from 'react';
import { useAwsCost } from '../../../services/awsService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

export function AwsCostPage() {
  const { data: cost, isLoading, error } = useAwsCost();

  if (isLoading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading AWS cost snapshot..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-md p-6">
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Unable to load cost analytics</h2>
        <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
      </div>
    );
  }

  if (!cost) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/40 border border-yellow-200 dark:border-yellow-700 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Cost data unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          Demo-based AWS cost intelligence is currently unavailable. Please try again shortly.
        </p>
      </div>
    );
  }

  const varianceClass = cost.summary.variance >= 0 ? 'text-red-500' : 'text-emerald-500';
  const optimizationPercent = (cost.summary.optimization_estimate / cost.summary.month_to_date_spend) * 100;

  return (
    <div className="space-y-10">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AWS Cost Intelligence</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl">
            High-level spend insights mirroring AWS Cost Explorer and Compute Optimizer signals. Values are populated from
            curated demo telemetry to match the GenAI CloudOps experience.
          </p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg px-5 py-4 text-sm text-blue-700 dark:text-blue-200">
          <div className="font-semibold flex items-center space-x-2">
            <i className="fas fa-wallet" />
            <span>Forecasted Spend</span>
          </div>
          <div className="mt-2 text-xl font-semibold text-blue-800 dark:text-blue-100">
            ${cost.summary.forecast_end_of_month.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
          <div className={`text-xs ${varianceClass}`}>
            Variance vs budget: {cost.summary.variance >= 0 ? '+' : ''}
            {cost.summary.variance.toLocaleString(undefined, { maximumFractionDigits: 2 })}%
          </div>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Month-to-date spend</span>
          <div className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">
            ${cost.summary.month_to_date_spend.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Budget</span>
          <div className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">
            ${cost.summary.budget.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Optimization potential</span>
          <div className="mt-3 text-2xl font-semibold text-emerald-500">
            ${cost.summary.optimization_estimate.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">≈ {optimizationPercent.toFixed(1)}% of MTD</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Trend guidance</span>
          <div className={`mt-3 text-lg font-semibold ${varianceClass}`}>
            {cost.summary.variance >= 0 ? 'Above budget' : 'Below budget'}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Monitor commitments and evaluate savings plans
          </p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Service Breakdown</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">Top AWS spend drivers</span>
          </div>
          <div className="space-y-4">
            {cost.service_breakdown.map((service) => (
              <div key={service.service}>
                <div className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
                  <span>{service.service}</span>
                  <span className="font-semibold">
                    ${service.spend.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="mt-2 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${service.change_percent >= 0 ? 'bg-red-400' : 'bg-emerald-400'}`}
                    style={{ width: `${Math.min(100, Math.abs(service.change_percent) * 3)}%` }}
                  />
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {service.change_percent >= 0 ? '+' : ''}
                  {service.change_percent.toFixed(1)}% month-over-month
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Optimization Recommendations</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">Compute Optimizer signals</span>
          </div>
          <ul className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
            {cost.recommendations.map((rec) => (
              <li key={rec.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{rec.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {rec.service} • {rec.term}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-emerald-500">
                    ${rec.potential_savings.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">{rec.details}</p>
              </li>
            ))}
            {cost.recommendations.length === 0 && (
              <li className="text-xs text-gray-500 dark:text-gray-400">No optimization items identified.</li>
            )}
          </ul>
        </div>
      </section>
    </div>
  );
}

export default AwsCostPage;
