import React from 'react';
import { useAwsSecurity } from '../../../services/awsService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

export function AwsSecurityPage() {
  const { data: security, isLoading, error } = useAwsSecurity();

  if (isLoading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading AWS security posture..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-md p-6">
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Unable to load security insights</h2>
        <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
      </div>
    );
  }

  if (!security) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/40 border border-yellow-200 dark:border-yellow-700 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Security snapshot unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          AWS Security Hub demo data is currently unavailable. Please try again shortly.
        </p>
      </div>
    );
  }

  const severityColors: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-200',
    HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-200',
    MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-200',
    LOW: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-200',
  };

  return (
    <div className="space-y-10">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AWS Security Posture</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl">
            Consolidated findings and IAM risk signals inspired by AWS Security Hub, GuardDuty, and IAM Access Analyzer.
            Demo data highlights the posture of critical workloads across your AWS accounts.
          </p>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-700 rounded-lg px-5 py-4 text-sm text-purple-700 dark:text-purple-200">
          <div className="font-semibold flex items-center space-x-2">
            <i className="fas fa-user-shield" />
            <span>Credential Exposure</span>
          </div>
          <div className="mt-2 text-xs">
            IAM users with keys: <strong>{security.summary.iam_users_with_keys}</strong>
          </div>
          <div className="text-xs">
            Unused security groups: <strong>{security.summary.unused_security_groups}</strong>
          </div>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Critical findings</span>
          <div className="mt-3 text-2xl font-semibold text-red-500">{security.summary.critical_findings}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">High findings</span>
          <div className="mt-3 text-2xl font-semibold text-orange-500">{security.summary.high_findings}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Medium findings</span>
          <div className="mt-3 text-2xl font-semibold text-yellow-500">{security.summary.medium_findings}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <span className="text-sm text-gray-500 dark:text-gray-400">Low findings</span>
          <div className="mt-3 text-2xl font-semibold text-blue-500">{security.summary.low_findings}</div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Security Findings</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">Top prioritized issues</span>
          </div>
          <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
            {security.findings.map((finding) => (
              <div key={finding.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{finding.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {finding.service} • {finding.resource}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${severityColors[finding.severity]}`}>
                    {finding.severity}
                  </span>
                </div>
                <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">{finding.details}</p>
                <div className="mt-3 text-xs text-blue-600 dark:text-blue-300">
                  <i className="fas fa-lightbulb mr-2"></i>
                  {finding.recommendation}
                </div>
              </div>
            ))}
            {security.findings.length === 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400">No findings detected.</p>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">IAM & RBAC Review</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">Role posture summary</span>
          </div>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Roles & Principals</h3>
              <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
                {security.rbac.roles.map((role) => (
                  <li key={role.name} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">{role.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Principals: {role.principals}</p>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">Last audited {role.last_audited}</span>
                    </div>
                    <p className="mt-2 text-xs text-purple-600 dark:text-purple-300">Risk: {role.risk}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Policies to Review</h3>
              <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
                {security.rbac.policies_to_review.map((policy) => (
                  <li key={policy.name} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-gray-900 dark:text-white">{policy.name}</p>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{policy.principal}</span>
                    </div>
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{policy.finding}</p>
                    <div className="mt-2 text-xs text-blue-600 dark:text-blue-300">
                      <i className="fas fa-lightbulb mr-2"></i>
                      {policy.recommendation}
                    </div>
                  </li>
                ))}
                {security.rbac.policies_to_review.length === 0 && (
                  <li className="text-xs text-gray-500 dark:text-gray-400">No policy reviews required.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AwsSecurityPage;
