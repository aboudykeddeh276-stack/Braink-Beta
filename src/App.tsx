/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { PanelLeft, PanelRight } from 'lucide-react';
import Sidebar from './components/Sidebar';
import AgentChat from './components/AgentChat';
import AgentActivity from './components/AgentActivity';
import VirtualFileSpace from './components/VirtualFileSpace';
import ServerRoom from './components/ServerRoom';
import BrainKEvolution from './components/BrainKEvolution';
import GoogleDriveApp from './components/GoogleDriveApp';
import WorkloadOrchestrator from './components/WorkloadOrchestrator';

export default function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isActivityOpen, setIsActivityOpen] = useState(false);
  const [activeView, setActiveView] = useState('chat');
  const [agentState, setAgentState] = useState({ type: 'IDLE', details: 'Awaiting input', activeTool: null });

  return (
    <div className="flex h-screen bg-white dark:bg-[#09090b] text-neutral-900 dark:text-neutral-100 overflow-hidden font-sans">
      
      {/* Left Sidebar */}
      <Sidebar isOpen={isSidebarOpen} activeView={activeView} setActiveView={setActiveView} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative h-full overflow-hidden">
        
        {/* Minimal Header */}
        <header className="h-14 flex items-center justify-between px-3 border-b border-border bg-white/80 dark:bg-[#09090b]/80 backdrop-blur-md z-10 shrink-0">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-lg text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            >
              <PanelLeft size={18} />
            </button>
            <span className="font-semibold text-sm">BrainK Workspace</span>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsActivityOpen(!isActivityOpen)}
              className={`p-2 rounded-lg transition-colors ${isActivityOpen ? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white' : 'text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
              title="Toggle Agent Activity"
            >
              <PanelRight size={18} />
            </button>
          </div>
        </header>

        {/* View Routing */}
        {activeView === 'chat' && <AgentChat onAgentAction={setAgentState} />}
        {activeView === 'fs' && <VirtualFileSpace />}
        {activeView === 'server' && <ServerRoom />}
        {activeView === 'evolution' && <BrainKEvolution />}
        {activeView === 'workloads' && (
          <div className="p-4 h-full flex-1">
            <WorkloadOrchestrator />
          </div>
        )}
        {activeView === 'drive' && (
          <div className="p-4 h-full flex-1">
            <GoogleDriveApp />
          </div>
        )}
      </div>

      {/* Right Side Activity Panel */}
      <AgentActivity isOpen={isActivityOpen} agentState={agentState} />

    </div>
  );
}

