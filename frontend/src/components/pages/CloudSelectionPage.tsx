import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCloudProviders } from '../../services/providerService';
import type { CloudProviderMetadata } from '../../services/providerService';
import { useCloudProvider } from '../../contexts/CloudProviderContext';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { OciLogo } from '../ui/icons/OciLogo';
import { AwsLogo } from '../ui/icons/AwsLogo';
import { AzureLogo } from '../ui/icons/AzureLogo';
import { GcpLogo } from '../ui/icons/GcpLogo';
import { OracleBrmLogo } from '../ui/icons/OracleBrmLogo';
import { SingleviewLogo } from '../ui/icons/SingleviewLogo';
import { EricssonBillingLogo } from '../ui/icons/EricssonBillingLogo';
import { AmdoxLogo } from '../ui/icons/AmdoxLogo';

const providerDestinations: Record<'oci' | 'aws', string> = {
  oci: '/dashboard',
  aws: '/aws/dashboard',
};

type ProviderOptionId = 'oci' | 'aws' | 'azure' | 'gcp';

interface ProviderOption {
  id: ProviderOptionId;
  name: string;
  description: string;
  logo: (props: { className?: string; title?: string }) => JSX.Element;
  disabled?: boolean;
  status?: string;
}

type ApplicationOptionId = 'oracle_brm' | 'singleview' | 'ericsson_billing' | 'amdox';

interface ApplicationOption {
  id: ApplicationOptionId;
  name: string;
  description: string;
  logo: (props: { className?: string; title?: string }) => JSX.Element;
  disabled?: boolean;
  status?: string;
}

const APPLICATION_FEATURES: Record<ApplicationOptionId, string[]> = {
  oracle_brm: [
    'Revenue assurance metrics',
    'Siebel/BRM integration health',
    'Payments & invoicing KPIs',
    'Customer experience signals',
  ],
  singleview: [],
  ericsson_billing: [],
  amdox: [],
};

type AdministrationOptionId = 'user_management' | 'role_management' | 'application_settings';

interface AdministrationOption {
  id: AdministrationOptionId;
  name: string;
  description: string;
  icon: string;
  disabled?: boolean;
  status?: string;
}

const ADMIN_FEATURES: Record<AdministrationOptionId, string[]> = {
  user_management: ['Invite or deactivate users', 'Manage MFA enrollment', 'Audit user login activity'],
  role_management: ['Create custom roles', 'Assign roles to users', 'Review privilege scopes'],
  application_settings: ['Update environment configuration', 'Toggle feature flags', 'Manage notification channels'],
};

export function CloudSelectionPage() {
  const navigate = useNavigate();
  const { provider, setProvider } = useCloudProvider();
  const { data: providers, isLoading, error } = useCloudProviders();
  const { logout, user, permissions } = useAuth();

  const [selectedProvider, setSelectedProvider] = React.useState<ProviderOptionId>(provider);
  const [selectedApplication, setSelectedApplication] = React.useState<ApplicationOptionId>('oracle_brm');
  const [selectedSecurityProvider, setSelectedSecurityProvider] = React.useState<ProviderOptionId>(provider);
  const [selectedAdministrationOption, setSelectedAdministrationOption] = React.useState<AdministrationOptionId>('user_management');

  React.useEffect(() => {
    setSelectedProvider(provider);
    if (provider === 'aws' || provider === 'oci') {
      setSelectedSecurityProvider(provider);
    }
  }, [provider]);

  const providerLookup = React.useMemo(() => {
    const map = new Map<'oci' | 'aws', CloudProviderMetadata>();
    providers?.forEach((cloud) => {
      if (cloud.id === 'oci' || cloud.id === 'aws') {
        map.set(cloud.id, cloud);
      }
    });
    return map;
  }, [providers]);

  const providerOptions = React.useMemo<ProviderOption[]>(
    () => [
      {
        id: 'aws',
        name: providerLookup.get('aws')?.name ?? 'Amazon Web Services',
        description:
          providerLookup.get('aws')?.description ??
          'Extensive cloud services platform designed for scalable infrastructure, observability, automation, and security.',
        logo: AwsLogo,
        status: providerLookup.get('aws')?.status ?? 'available',
      },
      {
        id: 'oci',
        name: providerLookup.get('oci')?.name ?? 'Oracle Cloud Infrastructure',
        description:
          providerLookup.get('oci')?.description ??
          'High-performance cloud foundation with integrated telemetry, cost insights, and automation for Oracle workloads.',
        logo: OciLogo,
        status: providerLookup.get('oci')?.status ?? 'available',
      },
      {
        id: 'azure',
        name: 'Microsoft Azure',
        description: 'Enterprise-ready cloud capabilities coming soon to the GenAI CloudOps experience.',
        logo: AzureLogo,
        disabled: true,
        status: 'coming-soon',
      },
      {
        id: 'gcp',
        name: 'Google Cloud Platform',
        description: 'Add Google Cloud operations to monitor workloads across multi-cloud environments (coming soon).',
        logo: GcpLogo,
        disabled: true,
        status: 'coming-soon',
      },
    ],
    [providerLookup]
  );

  const selectedMetadata = React.useMemo(() => {
    if (selectedProvider !== 'aws' && selectedProvider !== 'oci') {
      return undefined;
    }
    return providerLookup.get(selectedProvider);
  }, [providerLookup, selectedProvider]);

  const selectedFeatures = React.useMemo(() => {
    if (!selectedMetadata) {
      return [] as Array<[string, boolean]>;
    }
    return Object.entries(selectedMetadata.features ?? {});
  }, [selectedMetadata]);

  const selectedSecurityMetadata = React.useMemo(() => {
    if (selectedSecurityProvider !== 'aws' && selectedSecurityProvider !== 'oci') {
      return undefined;
    }
    return providerLookup.get(selectedSecurityProvider);
  }, [providerLookup, selectedSecurityProvider]);

  const selectedSecurityFeatures = React.useMemo(() => {
    if (!selectedSecurityMetadata) {
      return [] as Array<[string, boolean]>;
    }
    return Object.entries(selectedSecurityMetadata.features ?? {});
  }, [selectedSecurityMetadata]);

  const canContinue = selectedProvider === 'aws' || selectedProvider === 'oci';
  const canContinueApplication = selectedApplication === 'oracle_brm';
  const canContinueSecurity = selectedSecurityProvider === 'aws' || selectedSecurityProvider === 'oci';
  const canContinueAdministration = true;

  // Permission-based section visibility
  const hasInfrastructureAccess = React.useMemo(() => {
    return permissions?.can_view_dashboard || permissions?.can_view_cost_analyzer || false;
  }, [permissions]);

  const hasApplicationAccess = React.useMemo(() => {
    return permissions?.can_view_pod_analyzer || false;
  }, [permissions]);

  const hasSecurityAccess = React.useMemo(() => {
    return permissions?.can_view_access_analyzer || permissions?.can_approve_remediation || false;
  }, [permissions]);

  const hasAdministrationAccess = React.useMemo(() => {
    return permissions?.can_manage_users || permissions?.can_manage_roles || false;
  }, [permissions]);

  const handleContinue = () => {
    if (!canContinue) {
      return;
    }
    setProvider(selectedProvider);
    navigate(providerDestinations[selectedProvider]);
  };

  const handleSelectProvider = (providerId: string) => {
    if (providerId === 'aws' || providerId === 'oci') {
      setSelectedProvider(providerId);
    }
  };

  const applicationOptions = React.useMemo<ApplicationOption[]>(
    () => [
      {
        id: 'oracle_brm',
        name: 'Oracle BRM',
        description: 'Deep monitoring for Oracle Billing and Revenue Management workloads with demo dashboards.',
        logo: OracleBrmLogo,
        status: 'available',
      },
      {
        id: 'singleview',
        name: 'Singleview',
        description: 'Singleview operational telemetry is coming soon to the Application Monitoring experience.',
        logo: SingleviewLogo,
        disabled: true,
        status: 'coming-soon',
      },
      {
        id: 'ericsson_billing',
        name: 'Ericsson Billing',
        description: 'Ericsson billing dashboards will be available in an upcoming release.',
        logo: EricssonBillingLogo,
        disabled: true,
        status: 'coming-soon',
      },
      {
        id: 'amdox',
        name: 'Amdox',
        description: 'Amdox application monitoring is planned for future iterations of the suite.',
        logo: AmdoxLogo,
        disabled: true,
        status: 'coming-soon',
      },
    ],
    []
  );

  const selectedApplicationFeatures = React.useMemo(() => {
    return APPLICATION_FEATURES[selectedApplication] ?? [];
  }, [selectedApplication]);

  const handleSelectApplication = (applicationId: ApplicationOptionId) => {
    if (APPLICATION_FEATURES[applicationId]) {
      setSelectedApplication(applicationId);
    }
  };

  const handleContinueApplication = () => {
    if (!canContinueApplication) {
      return;
    }
    navigate('/operational-insights');
  };

  const handleSelectSecurityProvider = (providerId: string) => {
    if (providerId === 'aws' || providerId === 'oci') {
      setSelectedSecurityProvider(providerId);
    }
  };

  const handleContinueSecurity = () => {
    if (!canContinueSecurity) {
      return;
    }
    setProvider(selectedSecurityProvider as 'aws' | 'oci');
    navigate('/access-analyzer');
  };

  const administrationOptions = React.useMemo<AdministrationOption[]>(
    () => [
      {
        id: 'user_management',
        name: 'User Management',
        description: 'Invite new collaborators, adjust access levels, and oversee user lifecycle.',
        icon: 'fas fa-user-plus',
      },
      {
        id: 'role_management',
        name: 'Role Management',
        description: 'Define custom roles, align permissions, and assign responsibilities.',
        icon: 'fas fa-user-shield',
      },
      {
        id: 'application_settings',
        name: 'Application Settings',
        description: 'Update environment configurations and fine-tune product preferences.',
        icon: 'fas fa-sliders-h',
      },
    ],
    []
  );

  const selectedAdministrationFeatures = React.useMemo(() => {
    return ADMIN_FEATURES[selectedAdministrationOption];
  }, [selectedAdministrationOption]);

  const handleSelectAdministrationOption = (optionId: AdministrationOptionId) => {
    setSelectedAdministrationOption(optionId);
  };

  const handleContinueAdministration = () => {
    if (!canContinueAdministration) {
      return;
    }
    if (selectedAdministrationOption === 'user_management') {
      navigate('/user-management');
    } else {
      navigate('/settings');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading cloud providers..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-6 max-w-lg">
          <h2 className="text-lg font-semibold text-red-700 dark:text-red-200 mb-2">Unable to load providers</h2>
          <p className="text-sm text-red-600 dark:text-red-300">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="text-center flex-1">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Choose Your Cloud Environment</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Seamlessly switch between Oracle Cloud Infrastructure and Amazon Web Services. Each environment provides demo
            telemetry, cost insights, security posture, and automation capabilities aligned with the GenAI CloudOps
            experience.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.username}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
          </div>
          <button
            onClick={async () => {
              try {
                console.log('Sign out button clicked');
                await logout();
                console.log('Logout successful, navigating to login');
                navigate('/login');
              } catch (error) {
                console.error('Logout error:', error);
              }
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <i className="fas fa-sign-out-alt mr-2"></i>
            Sign Out
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {hasAdministrationAccess && (
          <section className="lg:col-span-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
            <div className="p-6 lg:p-8">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Administration</h2>
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200">
                      Identity &amp; Settings
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                    Manage your platform users, roles, and configuration with guided administration workflows.
                  </p>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                  <i className="fas fa-tools"></i>
                  <span>Administration console</span>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {administrationOptions.map((option) => (
                  <label
                    key={option.id}
                    className={`flex items-center justify-between rounded-lg border transition-all duration-200 ${selectedAdministrationOption === option.id
                      ? 'border-emerald-500 bg-emerald-50/60 dark:border-emerald-400 dark:bg-emerald-500/10 shadow-sm'
                      : 'border-gray-200 dark:border-gray-700 hover:border-emerald-400 hover:shadow'
                      }`}
                  >
                    <div className="flex items-center w-full p-4 gap-4">
                      <div className="relative flex items-center justify-center">
                        <input
                          type="radio"
                          name="administration"
                          value={option.id}
                          checked={selectedAdministrationOption === option.id}
                          onChange={() => handleSelectAdministrationOption(option.id)}
                          className="h-4 w-4 text-emerald-600 focus:ring-emerald-500"
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-base font-semibold text-gray-900 dark:text-white">{option.name}</p>
                        </div>
                        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{option.description}</p>
                      </div>
                      <div className="w-12 h-12 flex items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20">
                        <i className={`${option.icon} text-xl`}></i>
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              <div className="mt-8 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">Administrative actions</p>
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {selectedAdministrationFeatures.map((feature) => (
                    <div key={feature} className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full border border-emerald-400 bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
                        <i className="fas fa-check"></i>
                      </span>
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Administration tasks open the settings console in a guided configuration workspace.
                </div>
                <button
                  type="button"
                  onClick={handleContinueAdministration}
                  disabled={!canContinueAdministration}
                  className={`inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg shadow-sm transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 dark:focus:ring-offset-gray-900 ${canContinueAdministration
                    ? 'bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400'
                    : 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                    }`}
                >
                  Continue
                  <i className="fas fa-arrow-right ml-2"></i>
                </button>
              </div>
            </div>
          </section>
        )}

        {hasInfrastructureAccess && (
          <section className="lg:col-span-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
            <div className="p-6 lg:p-8">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Infrastructure Platform</h2>
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-200">
                      Multi-cloud
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                    Select the cloud provider you want to explore. Continue to open the tailored operational dashboard for that environment.
                  </p>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                  <i className="fas fa-layer-group"></i>
                  <span>GenAI CloudOps Infrastructure Suite</span>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {providerOptions.map((option) => {
                  const Logo = option.logo;
                  const isSelected = selectedProvider === option.id;
                  const statusLabel =
                    option.status === 'preview'
                      ? 'Preview'
                      : option.status === 'coming-soon'
                        ? 'Coming Soon'
                        : undefined;

                  return (
                    <label
                      key={option.id}
                      className={`flex items-center justify-between rounded-lg border transition-all duration-200 ${option.disabled
                        ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 cursor-not-allowed'
                        : isSelected
                          ? 'border-blue-500 bg-blue-50/60 dark:border-blue-400 dark:bg-blue-500/10 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-400 hover:shadow'
                        }`}
                    >
                      <div className="flex items-center w-full p-4 gap-4">
                        <div className="relative flex items-center justify-center">
                          <input
                            type="radio"
                            name="cloud-provider"
                            value={option.id}
                            disabled={option.disabled}
                            checked={isSelected}
                            onChange={() => handleSelectProvider(option.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                          />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-base font-semibold text-gray-900 dark:text-white">{option.name}</p>
                            {statusLabel && (
                              <span
                                className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full ${statusLabel === 'Preview'
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200'
                                  : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
                                  }`}
                              >
                                {statusLabel}
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{option.description}</p>
                        </div>
                        <Logo className="w-12 h-12 flex-shrink-0" />
                      </div>
                    </label>
                  );
                })}
              </div>

              <div className="mt-8 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">Feature coverage</p>
                {selectedFeatures.length > 0 ? (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedFeatures.map(([feature, enabled]) => (
                      <div key={feature} className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                        <span
                          className={`flex h-6 w-6 items-center justify-center rounded-full border text-xs ${enabled
                            ? 'border-green-400 bg-green-100 text-green-600 dark:bg-green-500/10 dark:text-green-300'
                            : 'border-gray-300 text-gray-400 dark:border-gray-600 dark:text-gray-500'
                            }`}
                        >
                          {enabled ? <i className="fas fa-check"></i> : <i className="fas fa-minus"></i>}
                        </span>
                        <span className="capitalize">{feature.replace(/_/g, ' ')}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Detailed capability mapping will be available once this provider is enabled.
                  </p>
                )}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Your selection is saved for quick access the next time you sign in.
                </div>
                <button
                  type="button"
                  onClick={handleContinue}
                  disabled={!canContinue}
                  className={`inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg shadow-sm transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 ${canContinue
                    ? 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400'
                    : 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                    }`}
                >
                  Continue
                  <i className="fas fa-arrow-right ml-2"></i>
                </button>
              </div>
            </div>
          </section>
        )}

        {hasApplicationAccess && (
          <section className="lg:col-span-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
            <div className="p-6 lg:p-8">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Application Monitoring</h2>
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-200">
                      Prototype
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                    Choose an application workload to explore demo monitoring dashboards. Continue to view aggregated alerts, health, and performance insights.
                  </p>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                  <i className="fas fa-desktop"></i>
                  <span>Operations telemetry suite</span>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {applicationOptions.map((option) => {
                  const Logo = option.logo;
                  const isSelected = selectedApplication === option.id;
                  const statusLabel = option.status === 'coming-soon' ? 'Coming Soon' : undefined;

                  return (
                    <label
                      key={option.id}
                      className={`flex items-center justify-between rounded-lg border transition-all duration-200 ${option.disabled
                        ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 cursor-not-allowed'
                        : isSelected
                          ? 'border-purple-500 bg-purple-50/60 dark:border-purple-400 dark:bg-purple-500/10 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:border-purple-400 hover:shadow'
                        }`}
                    >
                      <div className="flex items-center w-full p-4 gap-4">
                        <div className="relative flex items-center justify-center">
                          <input
                            type="radio"
                            name="application-monitoring"
                            value={option.id}
                            disabled={option.disabled}
                            checked={isSelected}
                            onChange={() => handleSelectApplication(option.id)}
                            className="h-4 w-4 text-purple-600 focus:ring-purple-500"
                          />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-base font-semibold text-gray-900 dark:text-white">{option.name}</p>
                            {statusLabel && (
                              <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200">
                                {statusLabel}
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{option.description}</p>
                        </div>
                        <Logo className="w-12 h-12 flex-shrink-0" />
                      </div>
                    </label>
                  );
                })}
              </div>

              <div className="mt-8 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">Highlighted capabilities</p>
                {selectedApplicationFeatures.length > 0 ? (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedApplicationFeatures.map((feature) => (
                      <div key={feature} className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-purple-400 bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-200">
                          <i className="fas fa-check"></i>
                        </span>
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Detailed capabilities will be revealed as this application becomes available in the monitoring suite.
                  </p>
                )}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Application previews currently use demo data for experience walkthroughs.
                </div>
                <button
                  type="button"
                  onClick={handleContinueApplication}
                  disabled={!canContinueApplication}
                  className={`inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg shadow-sm transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 dark:focus:ring-offset-gray-900 ${canContinueApplication
                    ? 'bg-purple-600 text-white hover:bg-purple-700 dark:bg-purple-500 dark:hover:bg-purple-400'
                    : 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                    }`}
                >
                  Continue
                  <i className="fas fa-arrow-right ml-2"></i>
                </button>
              </div>
            </div>
          </section>
        )}

        {hasSecurityAccess && (
          <section className="lg:col-span-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
            <div className="p-6 lg:p-8">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                <div>
                  <div className="flex items-center space-x-3">
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Security Monitoring</h2>
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-200">
                      Identity &amp; Access
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                    Choose the cloud provider to review security dashboards and monitoring features for your infrastructure.
                  </p>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                  <i className="fas fa-shield-alt"></i>
                  <span>Security posture overview</span>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {providerOptions.map((option) => {
                  const Logo = option.logo;
                  const isSelected = selectedSecurityProvider === option.id;
                  const statusLabel =
                    option.status === 'preview'
                      ? 'Preview'
                      : option.status === 'coming-soon'
                        ? 'Coming Soon'
                        : undefined;

                  return (
                    <label
                      key={`security-${option.id}`}
                      className={`flex items-center justify-between rounded-lg border transition-all duration-200 ${option.disabled
                        ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 cursor-not-allowed'
                        : isSelected
                          ? 'border-red-500 bg-red-50/60 dark:border-red-400 dark:bg-red-500/10 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:border-red-400 hover:shadow'
                        }`}
                    >
                      <div className="flex items-center w-full p-4 gap-4">
                        <div className="relative flex items-center justify-center">
                          <input
                            type="radio"
                            name="security-monitoring"
                            value={option.id}
                            disabled={option.disabled}
                            checked={isSelected}
                            onChange={() => handleSelectSecurityProvider(option.id)}
                            className="h-4 w-4 text-red-600 focus:ring-red-500"
                          />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-base font-semibold text-gray-900 dark:text-white">{option.name}</p>
                            {statusLabel && (
                              <span
                                className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full ${statusLabel === 'Preview'
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200'
                                  : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
                                  }`}
                              >
                                {statusLabel}
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{option.description}</p>
                        </div>
                        <Logo className="w-12 h-12 flex-shrink-0" />
                      </div>
                    </label>
                  );
                })}
              </div>

              <div className="mt-8 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wide">Security coverage</p>
                {selectedSecurityFeatures.length > 0 ? (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedSecurityFeatures.map(([feature, enabled]) => (
                      <div key={`security-feature-${feature}`} className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
                        <span
                          className={`flex h-6 w-6 items-center justify-center rounded-full border text-xs ${enabled
                            ? 'border-green-400 bg-green-100 text-green-600 dark:bg-green-500/10 dark:text-green-300'
                            : 'border-gray-300 text-gray-400 dark:border-gray-600 dark:text-gray-500'
                            }`}
                        >
                          {enabled ? <i className="fas fa-check"></i> : <i className="fas fa-minus"></i>}
                        </span>
                        <span className="capitalize">{feature.replace(/_/g, ' ')}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Detailed capability mapping will be available once this provider is enabled.
                  </p>
                )}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Review access risks, IAM posture, and remediation guidance in one unified view.
                </div>
                <button
                  type="button"
                  onClick={handleContinueSecurity}
                  disabled={!canContinueSecurity}
                  className={`inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg shadow-sm transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-gray-900 ${canContinueSecurity
                    ? 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-400'
                    : 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                    }`}
                >
                  Continue
                  <i className="fas fa-arrow-right ml-2"></i>
                </button>
              </div>
            </div>
          </section>
        )}

      </div>
    </div>
  );
}
