import React, { useState, useEffect } from 'react';
import { TemplateResponse, TemplateCategory } from '../../types/chatbot';
import { chatbotService } from '../../services/chatbotService';

interface TemplateSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onTemplateSelect: (template: TemplateResponse, variables?: Record<string, any>) => void;
}

export function TemplateSelector({ isOpen, onClose, onTemplateSelect }: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<TemplateCategory[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateResponse | null>(null);
  const [variables, setVariables] = useState<Record<string, any>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const templateResponse = await chatbotService.getTemplates();
      const categorized = chatbotService.categorizeTemplates(templateResponse);
      setTemplates(categorized);
    } catch (err) {
      setError('Failed to load templates');
      console.error('Error loading templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template: TemplateResponse) => {
    setSelectedTemplate(template);
    
    // Initialize variables from template
    const templateVariables = chatbotService.extractVariablesFromTemplate(template.template_text);
    const initialVariables: Record<string, any> = {};
    templateVariables.forEach(variable => {
      initialVariables[variable] = '';
    });
    setVariables(initialVariables);
  };

  const handleUseTemplate = () => {
    if (!selectedTemplate) return;

    // Validate variables
    const validation = chatbotService.validateTemplateVariables(selectedTemplate.template_text, variables);
    if (!validation.isValid) {
      setError(`Missing required variables: ${validation.missingVariables.join(', ')}`);
      return;
    }

    onTemplateSelect(selectedTemplate, variables);
    handleClose();
  };

  const handleClose = () => {
    setSelectedTemplate(null);
    setVariables({});
    setSearchQuery('');
    setSelectedCategory('');
    setError(null);
    onClose();
  };

  const filteredTemplates = templates.filter(category => {
    if (selectedCategory && category.name !== selectedCategory) return false;
    if (!searchQuery) return true;
    
    return category.templates.some(template =>
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const renderTemplateList = () => {
    return (
      <div className="space-y-4">
        {/* Search and filter */}
        <div className="space-y-3">
          <div className="relative">
            <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search templates..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {templates.map(category => (
              <option key={category.name} value={category.name}>
                {category.name} ({category.count})
              </option>
            ))}
          </select>
        </div>

        {/* Template categories */}
        <div className="max-h-96 overflow-y-auto space-y-4">
          {filteredTemplates.map(category => (
            <div key={category.name}>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                {category.name}
              </h4>
              <div className="space-y-2">
                {category.templates.map(template => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className="w-full text-left p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {template.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {template.description}
                        </div>
                        {template.requires_role && (
                          <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800 mt-2">
                            <i className="fas fa-lock mr-1"></i>
                            Requires: {template.requires_role}
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 ml-2">
                        Used {template.usage_count} times
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderTemplateForm = () => {
    if (!selectedTemplate) return null;

    const templateVariables = chatbotService.extractVariablesFromTemplate(selectedTemplate.template_text);
    const previewText = chatbotService.formatTemplateText(selectedTemplate.template_text, variables);

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2 mb-4">
          <button
            onClick={() => setSelectedTemplate(null)}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <i className="fas fa-arrow-left"></i>
          </button>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white">
              {selectedTemplate.name}
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {selectedTemplate.description}
            </p>
          </div>
        </div>

        {/* Variable inputs */}
        {templateVariables.length > 0 && (
          <div className="space-y-3">
            <h5 className="font-medium text-gray-900 dark:text-white">
              Fill in the required information:
            </h5>
            {templateVariables.map(variable => (
              <div key={variable}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {variable.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  type="text"
                  value={variables[variable] || ''}
                  onChange={(e) => setVariables(prev => ({
                    ...prev,
                    [variable]: e.target.value
                  }))}
                  placeholder={`Enter ${variable.replace('_', ' ')}`}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}
          </div>
        )}

        {/* Preview */}
        <div>
          <h5 className="font-medium text-gray-900 dark:text-white mb-2">Preview:</h5>
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border text-sm text-gray-700 dark:text-gray-300">
            {previewText}
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button
            onClick={handleUseTemplate}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Use Template
          </button>
          <button
            onClick={() => setSelectedTemplate(null)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Back
          </button>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {selectedTemplate ? 'Configure Template' : 'Select Template'}
            </h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-[calc(90vh-200px)]">
            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
              </div>
            )}

            {!loading && (selectedTemplate ? renderTemplateForm() : renderTemplateList())}
          </div>
        </div>
      </div>
    </>
  );
} 