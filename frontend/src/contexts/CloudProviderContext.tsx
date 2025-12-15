import React, { createContext, useContext, useMemo, useState } from 'react';

type CloudProviderId = 'oci' | 'aws';

interface CloudProviderContextValue {
  provider: CloudProviderId;
  setProvider: (provider: CloudProviderId) => void;
}

const DEFAULT_PROVIDER: CloudProviderId = 'oci';
const STORAGE_KEY = 'genai-cloudops:selected-provider';

const CloudProviderContext = createContext<CloudProviderContextValue | undefined>(undefined);

interface CloudProviderProviderProps {
  children: React.ReactNode;
}

export function CloudProviderProvider({ children }: CloudProviderProviderProps) {
  const [provider, setProviderState] = useState<CloudProviderId>(() => {
    if (typeof window === 'undefined') {
      return DEFAULT_PROVIDER;
    }
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY) as CloudProviderId | null;
      return stored === 'oci' || stored === 'aws' ? stored : DEFAULT_PROVIDER;
    } catch (error) {
      console.warn('Unable to read provider selection from storage:', error);
      return DEFAULT_PROVIDER;
    }
  });

  const setProvider = (nextProvider: CloudProviderId) => {
    setProviderState(nextProvider);
    try {
      window.localStorage.setItem(STORAGE_KEY, nextProvider);
    } catch (error) {
      console.warn('Unable to persist provider selection:', error);
    }
  };

  const value = useMemo(
    () => ({ provider, setProvider }),
    [provider]
  );

  return (
    <CloudProviderContext.Provider value={value}>
      {children}
    </CloudProviderContext.Provider>
  );
}

export function useCloudProvider(): CloudProviderContextValue {
  const context = useContext(CloudProviderContext);
  if (!context) {
    throw new Error('useCloudProvider must be used within a CloudProviderProvider');
  }
  return context;
}
