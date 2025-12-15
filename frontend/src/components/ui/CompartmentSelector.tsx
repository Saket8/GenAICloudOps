import React, { useState, useRef, useEffect, useMemo } from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export interface Compartment {
  id: string;
  name: string;
  description: string;
  lifecycle_state: string;
  compartment_id?: string;
  time_created?: string;
}

interface CompartmentSelectorProps {
  compartments: Compartment[];
  selectedCompartmentId: string;
  onCompartmentChange: (compartmentId: string) => void;
  loading?: boolean;
  label?: string;
}

export function CompartmentSelector({
  compartments,
  selectedCompartmentId,
  onCompartmentChange,
  loading,
  label = 'Select Compartment'
}: CompartmentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedCompartment = compartments.find(c => c.id === selectedCompartmentId);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Auto-expand path to selected compartment
  useEffect(() => {
    if (selectedCompartmentId && compartments.length > 0) {
      const newExpanded = new Set<string>();
      let current = compartments.find(c => c.id === selectedCompartmentId);

      // Traverse up adding all parents
      while (current && current.compartment_id) {
        newExpanded.add(current.compartment_id);
        current = compartments.find(c => c.id === current?.compartment_id);
      }

      setExpandedIds(prev => {
        const next = new Set(prev);
        newExpanded.forEach(id => next.add(id));
        return next;
      });
    }
  }, [selectedCompartmentId, compartments]);

  const toggleExpand = (e: React.MouseEvent, id: string) => {
    e.stopPropagation(); // Prevent dropdown item click
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Build hierarchical structure
  const { hierarchicalCompartments, compartmentMap } = useMemo(() => {
    if (!compartments || compartments.length === 0) {
      return { hierarchicalCompartments: [], compartmentMap: new Map() };
    }

    const hierarchy: (Compartment & { level: number; hasChildren: boolean; path: string })[] = [];
    const compMap = new Map(compartments.map(c => [c.id, c]));

    // Build parent-child relationships
    const childrenMap = new Map<string, Compartment[]>();
    compartments.forEach(c => {
      const parentId = c.compartment_id || 'ROOT';
      if (!childrenMap.has(parentId)) {
        childrenMap.set(parentId, []);
      }
      childrenMap.get(parentId)!.push(c);
    });

    // Find root compartments
    const roots = compartments.filter(c => {
      if (!c.compartment_id) return true;
      const parentExists = compMap.has(c.compartment_id);
      return !parentExists;
    });

    const addToHierarchy = (comp: Compartment, level: number = 0, parentPath: string = '') => {
      const children = childrenMap.get(comp.id) || [];
      const hasChildren = children.length > 0;
      const currentPath = parentPath ? `${parentPath} > ${comp.name}` : comp.name;

      hierarchy.push({ ...comp, level, hasChildren, path: currentPath });

      children
        .sort((a, b) => a.name.localeCompare(b.name))
        .forEach(child => addToHierarchy(child, level + 1, currentPath));
    };

    roots
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach(root => addToHierarchy(root, 0, ''));

    // Handle orphans
    const processedIds = new Set(hierarchy.map(h => h.id));
    const orphaned = compartments
      .filter(comp => !processedIds.has(comp.id))
      .sort((a, b) => a.name.localeCompare(b.name));

    if (orphaned.length > 0) {
      orphaned.forEach(comp => hierarchy.push({ ...comp, level: 0, hasChildren: false, path: comp.name }));
    }

    return { hierarchicalCompartments: hierarchy, compartmentMap: compMap };
  }, [compartments]);


  // Filter for display based on Expansion AND Search
  const displayCompartments = useMemo(() => {
    if (!searchTerm) {
      // If no search, respect expansion state
      return hierarchicalCompartments.filter(comp => {
        // If root, always visible
        if (comp.level === 0) return true;

        // Use compartment_id (parent) to check visibility recursively
        let parentId = comp.compartment_id;
        while (parentId) {
          // If parent is not expanded, hide this child
          if (!expandedIds.has(parentId)) return false;

          // Move up to grandparent
          const parent = compartmentMap.get(parentId);
          // If we hit a root (or orphan top) logic
          if (!parent || !parent.compartment_id || !compartmentMap.has(parent.compartment_id)) {
            break;
          }
          parentId = parent.compartment_id;
        }
        return true;
      });
    } else {
      // If searching, flatten tree (ignore expansion) to show all matches
      return hierarchicalCompartments.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.path.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
  }, [hierarchicalCompartments, expandedIds, searchTerm, compartmentMap]);


  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <LoadingSpinner size="sm" />
        <span className="text-sm text-gray-500 dark:text-gray-400">Loading compartments...</span>
      </div>
    );
  }

  // Get stats
  const maxLevel = Math.max(...hierarchicalCompartments.map(c => c.level), 0);
  const rootCount = hierarchicalCompartments.filter(c => c.level === 0).length;

  return (
    <div className="relative" ref={dropdownRef}>
      <label htmlFor="compartment-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {label}
      </label>
      <div className="relative">
        {/* Custom Dropdown Button */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="block w-full pl-3 pr-10 py-2.5 text-base border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-left shadow-sm truncate"
          title={selectedCompartment?.name || "Select Compartment"}
        >
          {selectedCompartment ? (
            <span className="flex items-center">
              <span className={`inline-block w-2 h-2 rounded-full mr-2 flex-shrink-0 ${selectedCompartment.lifecycle_state === 'ACTIVE' ? 'bg-green-500' : 'bg-gray-400'
                }`}></span>
              <span className="truncate">{selectedCompartment.name}</span>
            </span>
          ) : (
            <span className="text-gray-500">Select a compartment...</span>
          )}
        </button>

        {/* Dropdown Arrow */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <i className={`fas fa-chevron-${isOpen ? 'up' : 'down'} text-gray-400 text-sm transition-transform duration-200`}></i>
        </div>

        {/* Custom Dropdown Menu */}
        {isOpen && (
          <div className="absolute z-50 mt-1 right-0 min-w-[100%] w-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl max-h-96 overflow-hidden flex flex-col">
            {/* Search Box */}
            <div className="p-2 border-b border-gray-200 dark:border-gray-600 flex-shrink-0">
              <div className="relative">
                <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input
                  type="text"
                  placeholder="Search compartments..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Compartment List */}
            <div className="overflow-y-auto flex-grow">
              {displayCompartments.length === 0 ? (
                <div className="px-4 py-3 text-gray-500 dark:text-gray-400 text-sm text-center">
                  {compartments.length === 0
                    ? "No compartments found"
                    : "No matches found"}
                </div>
              ) : (
                displayCompartments.map((compartment) => {
                  const isSelected = compartment.id === selectedCompartmentId;
                  const isExpanded = expandedIds.has(compartment.id);

                  return (
                    <div
                      key={compartment.id}
                      className={`flex items-center w-full hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors duration-150 border-l-4 ${isSelected
                          ? 'bg-blue-50 dark:bg-blue-900/30 border-l-blue-500'
                          : 'border-l-transparent hover:border-l-gray-300'
                        }`}
                    >
                      {/* Indentation Spacer */}
                      <div style={{ width: `${12 + compartment.level * 24}px` }} className="flex-shrink-0"></div>

                      {/* Expand/Collapse Toggle */}
                      <div className="w-5 flex-shrink-0 flex justify-center">
                        {compartment.hasChildren && !searchTerm && (
                          <button
                            type="button"
                            onClick={(e) => toggleExpand(e, compartment.id)}
                            className="text-gray-400 hover:text-blue-500 focus:outline-none p-0.5"
                          >
                            <i className={`fas fa-${isExpanded ? 'minus-square' : 'plus-square'} text-xs`}></i>
                          </button>
                        )}
                      </div>

                      {/* Main Clickable Area */}
                      <button
                        type="button"
                        onClick={() => {
                          onCompartmentChange(compartment.id);
                          setIsOpen(false);
                          setSearchTerm('');
                        }}
                        className="flex-1 text-left py-2.5 text-sm whitespace-nowrap pr-4 flex items-center"
                        title={compartment.path}
                      >
                        {/* Icon based on type */}
                        <span className="mr-2 text-center w-5 flex-shrink-0">
                          {compartment.level === 0 ? (
                            <i className="fas fa-building text-blue-500" title="Root/Tenancy"></i>
                          ) : compartment.hasChildren ? (
                            <i className={`fas fa-folder${isExpanded ? '-open' : ''} text-yellow-500`} title="Parent Compartment"></i>
                          ) : (
                            <i className="fas fa-cube text-gray-400" title="Compartment"></i>
                          )}
                        </span>

                        {/* Status Dot */}
                        <span className={`inline-block w-2 h-2 rounded-full mr-2 flex-shrink-0 ${compartment.lifecycle_state === 'ACTIVE' ? 'bg-green-500' : 'bg-gray-400'
                          }`}></span>

                        {/* Name */}
                        <span className={`mr-2 ${compartment.level === 0
                            ? 'font-semibold text-gray-900 dark:text-white'
                            : compartment.hasChildren
                              ? 'font-medium text-gray-800 dark:text-gray-200'
                              : 'text-gray-700 dark:text-gray-300'
                          }`}>
                          {compartment.name}
                        </span>

                        {/* Selected Check */}
                        {isSelected && (
                          <i className="fas fa-check text-blue-500 text-xs ml-1"></i>
                        )}
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-600 text-xs text-gray-500 dark:text-gray-400 flex justify-between flex-shrink-0">
              <span>{compartments.length} compartments</span>
              <span>{maxLevel + 1} levels</span>
            </div>
          </div>
        )}
      </div>

      {/* Selected Info */}
      {selectedCompartment && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 truncate">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs flex-shrink-0 ${selectedCompartment.lifecycle_state === 'ACTIVE'
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}>
              {selectedCompartment.lifecycle_state}
            </span>
            <span className="truncate" title={selectedCompartment.description || ''}>
              {selectedCompartment.description}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}