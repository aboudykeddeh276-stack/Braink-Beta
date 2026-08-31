import React from 'react';
import { MessageSquare, Plus, Settings, Folder, Search, HardDrive, Cpu, BrainCircuit, MonitorPlay } from 'lucide-react';
import { motion } from 'motion/react';

export default function Sidebar({ isOpen, activeView, setActiveView }: { isOpen: boolean; activeView: string; setActiveView: (view: string) => void }) {
  return (
    <motion.div
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: isOpen ? 260 : 0, opacity: isOpen ? 1 : 0 }}
      transition={{ type: "spring", bounce: 0, duration: 0.3 }}
      className={`h-full bg-neutral-50 dark:bg-neutral-900 border-r border-border flex flex-col flex-shrink-0 overflow-hidden ${isOpen ? 'w-[260px]' : 'w-0'}`}
    >
      <div className="p-3 flex items-center justify-between">
        <button 
          onClick={() => setActiveView('chat')}
          className="flex-1 flex items-center gap-2 px-3 py-2 bg-white dark:bg-neutral-800 border border-border rounded-lg shadow-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors text-sm font-medium">
          <Plus size={16} />
          New Agent Session
        </button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar px-3 py-2 flex flex-col gap-1">
        <div className="text-xs font-semibold tracking-wider text-neutral-500 dark:text-neutral-400 px-2 py-2 mt-2">VIRTUAL ENVIRONMENT</div>
        
        <button 
          onClick={() => setActiveView('chat')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'chat' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <MessageSquare size={16} className={activeView === 'chat' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">Agent Terminal</span>
        </button>

        <button 
          onClick={() => setActiveView('fs')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'fs' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <HardDrive size={16} className={activeView === 'fs' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">Virtual File Space</span>
        </button>

        <button 
          onClick={() => setActiveView('server')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'server' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <Cpu size={16} className={activeView === 'server' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">Server Room</span>
        </button>
        
        <button 
          onClick={() => setActiveView('evolution')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'evolution' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <BrainCircuit size={16} className={activeView === 'evolution' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">BrainK Evolution</span>
        </button>

        <button 
          onClick={() => setActiveView('workloads')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'workloads' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <MonitorPlay size={16} className={activeView === 'workloads' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">Virtual Hardware</span>
        </button>

        <div className="text-xs font-semibold tracking-wider text-neutral-500 dark:text-neutral-400 px-2 py-2 mt-2">INTEGRATIONS</div>

        <button 
          onClick={() => setActiveView('drive')}
          className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-left transition-colors ${activeView === 'drive' ? 'bg-neutral-200/50 dark:bg-neutral-800 text-neutral-900 dark:text-white font-medium' : 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300'}`}>
          <HardDrive size={16} className={activeView === 'drive' ? 'text-indigo-500' : 'text-neutral-500 shrink-0'} />
          <span className="truncate">Google Drive</span>
        </button>

      </div>

      <div className="p-3 border-t border-border mt-auto flex flex-col gap-1">
        <button className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 text-neutral-600 dark:text-neutral-300 text-sm transition-colors">
          <Settings size={16} className="text-neutral-500 shrink-0" />
          Settings
        </button>
        
        <div className="mt-2 px-2 py-2 flex items-center gap-3 hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50 rounded-lg cursor-pointer transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-medium text-sm shadow-inner shrink-0">
            BK
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-sm font-medium truncate text-neutral-900 dark:text-neutral-100">BrainK Workspace</span>
            <span className="text-xs text-neutral-500 truncate">Pro Tier</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
