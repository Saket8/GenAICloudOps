import React from 'react';
import { useAwsAutomation } from '../../../services/awsService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

export function AwsAutomationPage() {
  const { data: automation, isLoading, error } = useAwsAutomation();

  if (isLoading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading AWS automation playbooks..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-md p-6">
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Unable to load automation data</h2>
        <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
      </div>
    );
  }

  if (!automation) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/40 border border-yellow-200 dark:border-yellow-700 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Automation snapshot unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          AWS Systems Manager demo playbooks are currently unavailable. Please try again shortly.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AWS Automation & Runbooks</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl">
            Demo catalogue of AWS Systems Manager and Lambda-driven playbooks used for remediation and operational
            excellence. Each item follows the GenAI CloudOps layout for consistent operator workflows.
          </p>
        </div>
        <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-lg px-5 py-4 text-sm text-amber-700 dark:text-amber-200">
          <div className="font-semibold flex items-center space-x-2">
            <i className="fas fa-user-check" />
            <span>Approval Workflow</span>
          </div>
          <div className="mt-2 text-xs">
            Pending approvals: <strong>{automation.approvals.pending}</strong>
          </div>
          <div className="text-xs">
            Required approvers: {automation.approvals.approvers.join(', ')}
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        {automation.playbooks.map((playbook) => (
          <div key={playbook.id} className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{playbook.name}</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mt-1">
                  {playbook.category}
                </p>
              </div>
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-200">
                Risk {playbook.risk}
              </span>
            </div>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-300 leading-6">{playbook.description}</p>
            <div className="mt-6">
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                Execution Steps
              </h3>
              <ol className="space-y-2 text-sm text-gray-700 dark:text-gray-300 list-decimal list-inside">
                {playbook.steps.map((step, index) => (
                  <li key={`${playbook.id}-step-${index}`}>{step}</li>
                ))}
              </ol>
            </div>
            <div className="mt-6 text-xs text-gray-500 dark:text-gray-400">
              Last validated: {new Date(playbook.last_validated).toLocaleDateString()}
            </div>
            <button className="mt-6 inline-flex items-center px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400">
              <i className="fas fa-play mr-2" />
              Stage Runbook
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}

export default AwsAutomationPage;
