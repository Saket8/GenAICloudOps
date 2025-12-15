import React, { useState } from 'react';

interface ResourceFilterProps {
  onSearchChange: (search: string) => void;
  onStatusFilter: (status: string) => void;
  onResourceTypeFilter: (type: string) => void;
  searchTerm: string;
  selectedStatus: string;
  selectedResourceType: string;
}

export function ResourceFilter({
  onSearchChange,
  onStatusFilter,
  onResourceTypeFilter,
  searchTerm,
  selectedStatus,
  selectedResourceType
}: ResourceFilterProps) {
  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'ACTIVE', label: 'Active' },
    { value: 'RUNNING', label: 'Running' },
    { value: 'STOPPED', label: 'Stopped' },
    { value: 'INACTIVE', label: 'Inactive' },
    { value: 'FAILED', label: 'Failed' },
    { value: 'ERROR', label: 'Error' }
  ];

  const resourceTypeOptions = [
    { value: '', label: 'All Resources' },
    { value: 'compute_instances', label: 'Compute Instances' },
    { value: 'databases', label: 'Databases' },
    { value: 'oke_clusters', label: 'OKE Clusters' },
    { value: 'api_gateways', label: 'API Gateways' },
    { value: 'load_balancers', label: 'Load Balancers' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
        {/* Search Input */}
        <div className="flex-1 max-w-md">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Search Resources
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <i className="fas fa-search text-gray-400"></i>
            </div>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search by name, ID, or description..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
            {searchTerm && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <i className="fas fa-times text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"></i>
              </button>
            )}
          </div>
        </div>

        {/* Status Filter */}
        <div className="min-w-[160px]">
          <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Filter by Status
          </label>
          <select
            id="status-filter"
            value={selectedStatus}
            onChange={(e) => onStatusFilter(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Resource Type Filter */}
        <div className="min-w-[180px]">
          <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Filter by Type
          </label>
          <select
            id="type-filter"
            value={selectedResourceType}
            onChange={(e) => onResourceTypeFilter(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            {resourceTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clear Filters */}
        {(searchTerm || selectedStatus || selectedResourceType) && (
          <div className="flex items-end">
            <button
              onClick={() => {
                onSearchChange('');
                onStatusFilter('');
                onResourceTypeFilter('');
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            >
              <i className="fas fa-times mr-2"></i>
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Active Filters Summary */}
      {(searchTerm || selectedStatus || selectedResourceType) && (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">Active filters:</span>
          {searchTerm && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              Search: "{searchTerm}"
              <button
                onClick={() => onSearchChange('')}
                className="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
              >
                <i className="fas fa-times text-xs"></i>
              </button>
            </span>
          )}
          {selectedStatus && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              Status: {statusOptions.find(o => o.value === selectedStatus)?.label}
              <button
                onClick={() => onStatusFilter('')}
                className="ml-1 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
              >
                <i className="fas fa-times text-xs"></i>
              </button>
            </span>
          )}
          {selectedResourceType && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
              Type: {resourceTypeOptions.find(o => o.value === selectedResourceType)?.label}
              <button
                onClick={() => onResourceTypeFilter('')}
                className="ml-1 text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-200"
              >
                <i className="fas fa-times text-xs"></i>
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
} 