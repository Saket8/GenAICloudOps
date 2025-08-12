import React, { useState } from 'react';

interface GeneralSettings {
  environment: 'development' | 'staging' | 'production';
  apiBaseUrl: string;
  appVersion: string;
}

interface FeatureFlags {
  aiInsights: boolean;
  autoRemediation: boolean;
  useMockData: boolean;
  enableWebsocket: boolean;
}

interface NotificationSettings {
  emailOnCritical: boolean;
  emailAddress: string;
  slackEnabled: boolean;
  slackWebhookMasked: string;
}

interface SecuritySettings {
  mfaEnabled: boolean;
  tokenExpiryMinutes: number;
  passwordPolicy: 'lenient' | 'standard' | 'strict';
}

export function SettingsPage() {
  const [general, setGeneral] = useState<GeneralSettings>({
    environment: 'development',
    apiBaseUrl: 'http://localhost:8000/api/v1',
    appVersion: '1.0.0',
  });

  const [features, setFeatures] = useState<FeatureFlags>({
    aiInsights: true,
    autoRemediation: false,
    useMockData: true,
    enableWebsocket: false,
  });

  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailOnCritical: true,
    emailAddress: 'alerts@example.com',
    slackEnabled: true,
    slackWebhookMasked: 'https://hooks.slack.com/services/****/****/********',
  });

  const [security, setSecurity] = useState<SecuritySettings>({
    mfaEnabled: true,
    tokenExpiryMinutes: 60,
    passwordPolicy: 'standard',
  });

  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save latency
    setTimeout(() => {
      setSaving(false);
      setSavedAt(new Date().toLocaleTimeString());
      alert('✅ Settings saved (dummy). These changes are not persisted.');
    }, 800);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              <i className="fas fa-cog mr-2 text-blue-500"></i>
              Settings
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Configure application preferences (dummy data)
            </p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium disabled:opacity-50"
          >
            {saving ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                Saving...
              </>
            ) : (
              <>
                <i className="fas fa-save mr-2"></i>
                Save Changes
              </>
            )}
          </button>
        </div>
        {savedAt && (
          <div className="mt-2 text-xs text-green-600 dark:text-green-400">
            Last saved at {savedAt}
          </div>
        )}
      </div>

      {/* General Settings */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">General</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">Environment</label>
            <select
              value={general.environment}
              onChange={(e) => setGeneral({ ...general, environment: e.target.value as GeneralSettings['environment'] })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            >
              <option value="development">Development</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">API Base URL</label>
            <input
              value={general.apiBaseUrl}
              onChange={(e) => setGeneral({ ...general, apiBaseUrl: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">App Version</label>
            <input
              value={general.appVersion}
              onChange={(e) => setGeneral({ ...general, appVersion: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Feature Flags */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Feature Flags</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { key: 'aiInsights', label: 'Enable AI Insights' },
            { key: 'autoRemediation', label: 'Enable Auto-Remediation' },
            { key: 'useMockData', label: 'Use Mock Data (MSW)' },
            { key: 'enableWebsocket', label: 'Enable WebSocket (DEV)' },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={(features as any)[key]}
                onChange={(e) => setFeatures({ ...features, [key]: e.target.checked } as FeatureFlags)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-800 dark:text-gray-200">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Notifications</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={notifications.emailOnCritical}
              onChange={(e) => setNotifications({ ...notifications, emailOnCritical: e.target.checked })}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-800 dark:text-gray-200">Email on Critical Alerts</span>
          </label>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">Alert Email</label>
            <input
              value={notifications.emailAddress}
              onChange={(e) => setNotifications({ ...notifications, emailAddress: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={notifications.slackEnabled}
              onChange={(e) => setNotifications({ ...notifications, slackEnabled: e.target.checked })}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-800 dark:text-gray-200">Slack Notifications</span>
          </label>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">Slack Webhook</label>
            <input
              value={notifications.slackWebhookMasked}
              onChange={(e) => setNotifications({ ...notifications, slackWebhookMasked: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Security</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={security.mfaEnabled}
              onChange={(e) => setSecurity({ ...security, mfaEnabled: e.target.checked })}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-800 dark:text-gray-200">Require MFA</span>
          </label>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">Token Expiry (minutes)</label>
            <input
              type="number"
              min={5}
              max={720}
              value={security.tokenExpiryMinutes}
              onChange={(e) => setSecurity({ ...security, tokenExpiryMinutes: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-300 mb-1">Password Policy</label>
            <select
              value={security.passwordPolicy}
              onChange={(e) => setSecurity({ ...security, passwordPolicy: e.target.value as SecuritySettings['passwordPolicy'] })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            >
              <option value="lenient">Lenient</option>
              <option value="standard">Standard</option>
              <option value="strict">Strict</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage; 