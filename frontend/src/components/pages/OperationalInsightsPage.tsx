import React, { useState } from 'react';
import { OciLogo } from '../ui/icons/OciLogo';

const grafanaDemoUrl =
  'https://play.grafana.org/d/000000012/grafana-play-home?orgId=1&kiosk=1&refresh=30s';

interface ServiceTile {
  name: string;
  description: string;
  status: 'Operational' | 'Degraded' | 'Maintenance';
  owner: string;
  notes: string;
}

const serviceTiles: ServiceTile[] = [
  {
    name: 'Oracle BRM Core',
    description: 'Charging, billing, and payment orchestration services',
    status: 'Operational',
    owner: 'Billing Platform Team',
    notes: 'Synthetic heartbeat checks passing. No open incidents.',
  },
  {
    name: 'Oracle ECE Rating',
    description: 'Real-time rating pipelines for usage consumption events',
    status: 'Operational',
    owner: 'Usage Services Team',
    notes: 'Kafka ingress stable. Latency under 250ms (dummy metric).',
  },
  {
    name: 'Revenue Assurance',
    description: 'Anomaly detection and revenue leakage safeguards',
    status: 'Maintenance',
    owner: 'Finance Ops',
    notes: 'Planned analytics model refresh underway (dummy window).',
  },
];

const statusColorMap: Record<typeof serviceTiles[number]['status'], string> = {
  Operational: 'bg-green-500',
  Degraded: 'bg-amber-500',
  Maintenance: 'bg-purple-500',
};

export function OperationalInsightsPage() {
  const [selectedService, setSelectedService] = useState<ServiceTile | null>(null);

  const handleServiceClick = (service: ServiceTile) => {
    setSelectedService(service);
  };

  const closeDashboard = () => {
    setSelectedService(null);
  };
  return (
    <div className="space-y-6">
      <header className="bg-white dark:bg-gray-800 shadow rounded-xl p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-start md:items-center gap-4">
          <div className="bg-red-50 dark:bg-red-900/40 rounded-lg p-3">
            <OciLogo className="w-10 h-10" title="Oracle Operational Insights" />
          </div>
          <div>
            <p className="text-sm uppercase tracking-wide text-red-600 dark:text-red-300 font-semibold">
              Oracle Communications
            </p>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              BRM &amp; ECE Operational Insights (Prototype)
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 max-w-2xl">
              This experience embeds a Grafana dashboard with dummy telemetry for API throughput, CDR processing,
              payment success, and usage workloads across Oracle Billing and Revenue Management (BRM) and Elastic
              Charging Engine (ECE).
            </p>
          </div>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/40 border border-purple-200 dark:border-purple-700 rounded-lg p-4 max-w-xs text-sm text-purple-900 dark:text-purple-100">
          <p className="font-semibold flex items-center gap-2">
            <i className="fas fa-lightbulb text-purple-500"></i>
            Prototype Notice
          </p>
          <p className="mt-1">
            All data in this view is mocked for concept validation. Replace the Grafana URL and service metadata
            when integrating with production systems.
          </p>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        {serviceTiles.map((service) => (
          <button
            key={service.name}
            onClick={() => handleServiceClick(service)}
            className="text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 flex flex-col gap-3 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md transition-all duration-200 group w-full"
          >
            <div className="flex items-start justify-between w-full">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                  {service.name}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-300">{service.description}</p>
              </div>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold text-white ${statusColorMap[service.status]
                  }`}
              >
                {service.status}
              </span>
            </div>
            <dl className="text-sm space-y-1 text-gray-600 dark:text-gray-300 w-full">
              <div className="flex items-center gap-2">
                <dt className="font-medium text-gray-500 dark:text-gray-400">Service owner:</dt>
                <dd>{service.owner}</dd>
              </div>
              <div className="flex items-start gap-2">
                <dt className="font-medium text-gray-500 dark:text-gray-400">Notes:</dt>
                <dd className="flex-1">{service.notes}</dd>
              </div>
            </dl>
          </button>
        ))}
      </section>

      {/* Grafana Dashboard Modal */}
      {selectedService && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={closeDashboard}></div>

            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                    {selectedService.name} - Analytics
                  </h3>
                  <button
                    onClick={closeDashboard}
                    className="bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <span className="sr-only">Close</span>
                    <i className="fas fa-times text-xl"></i>
                  </button>
                </div>
                <div className="w-full h-[600px] bg-gray-100 dark:bg-gray-900 rounded-lg flex items-center justify-center border border-gray-200 dark:border-gray-700 relative overflow-hidden">
                  {/* Placeholder for Grafana Dashboard */}
                  <div className="text-center">
                    <div className="mb-4">
                      <i className="fas fa-chart-area text-6xl text-gray-300 dark:text-gray-600"></i>
                    </div>
                    <h4 className="text-xl font-semibold text-gray-700 dark:text-gray-300">Grafana Dashboard</h4>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      Visualizing metrics for {selectedService.name}
                    </p>
                    <div className="mt-6 animate-pulse flex justify-center">
                      <div className="h-2 w-24 bg-blue-400 rounded"></div>
                    </div>
                  </div>

                  {/* Simulated Iframe Overlay (Optional for realism) */}
                  <div className="absolute inset-0 bg-gradient-to-br from-transparent to-gray-50/10 pointer-events-none"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}



      <section className="grid gap-4 md:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <i className="fas fa-clipboard-check text-blue-500"></i>
            Runbook Links
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-blue-600 dark:text-blue-400">
            <li>
              <a href="#" className="hover:underline">
                BRM Billing Pipeline Recovery (dummy link)
              </a>
            </li>
            <li>
              <a href="#" className="hover:underline">
                ECE Kafka Lag Triage Checklist (dummy link)
              </a>
            </li>
            <li>
              <a href="#" className="hover:underline">
                Payment Gateway Fallback Playbook (dummy link)
              </a>
            </li>
          </ul>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <i className="fas fa-layer-group text-emerald-500"></i>
            Integration Checklist
          </h3>
          <ol className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-300 list-decimal list-inside">
            <li>Replace Grafana URL with tenant PROM endpoint.</li>
            <li>Connect BRM/ECE data sources via secure service account.</li>
            <li>Parameterise environment switcher (DEV / QA / PROD).</li>
            <li>Configure SSO or embed tokens for Grafana viewer role.</li>
          </ol>
        </div>
      </section>
    </div>
  );
}
