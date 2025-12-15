import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { api } from './apiClient';

export interface CloudProviderMetadata {
  id: 'oci' | 'aws' | string;
  name: string;
  description: string;
  region_defaults: Record<string, string>;
  features: Record<string, boolean>;
  status: 'available' | 'preview' | 'beta' | string;
}

const providerQueryKeys = {
  all: ['cloud-providers'] as const,
};

async function fetchCloudProviders(): Promise<CloudProviderMetadata[]> {
  const response = await api.get<CloudProviderMetadata[]>('/providers');
  return response.data;
}

export function useCloudProviders(): UseQueryResult<CloudProviderMetadata[], Error> {
  return useQuery({
    queryKey: providerQueryKeys.all,
    queryFn: fetchCloudProviders,
    staleTime: 10 * 60 * 1000,
  });
}
