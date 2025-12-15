import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Navigation } from './Navigation';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatbotPanel } from './ChatbotPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0a1628]">
      {/* Main Application Container */}
      <div className="flex h-screen overflow-hidden">

        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Header */}
          <Header
            user={user}
            onMenuClick={() => setSidebarOpen(!sidebarOpen)}
            onChatbotToggle={() => setChatbotOpen(!chatbotOpen)}
          />

          {/* Navigation Tabs */}
          <Navigation />

          {/* Page Content */}
          <main className="flex-1 overflow-auto bg-[#0d1b3a] dark:bg-[#0a1428]">
            <div className="p-6">
              {children}
            </div>
          </main>
        </div>

        {/* Chatbot Panel */}
        {chatbotOpen && (
          <ChatbotPanel
            isOpen={chatbotOpen}
            onClose={() => setChatbotOpen(false)}
          />
        )}
      </div>
    </div>
  );
} 