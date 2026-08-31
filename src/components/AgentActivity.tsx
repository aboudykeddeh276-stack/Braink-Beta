import React from 'react';
import { Activity, Terminal, Code2, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export default function AgentActivity({ isOpen, agentState }: { isOpen: boolean; agentState: any }) {
  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: 320, opacity: 1 }}
      exit={{ width: 0, opacity: 0 }}
      className="h-full bg-white dark:bg-[#09090b] border-l border-border flex flex-col flex-shrink-0"
    >
      <div className="h-14 border-b border-border flex items-center px-4 font-medium text-sm text-neutral-800 dark:text-neutral-200">
        <Activity size={16} className="mr-2 text-neutral-500" />
        Agent Activity
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-4">
        
        {/* State Card */}
        <div className="border border-border rounded-xl p-4 bg-neutral-50 dark:bg-neutral-800/50 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Current Status</span>
            {agentState.type !== 'IDLE' && agentState.type !== 'ERROR' && (
              <Loader2 size={14} className="animate-spin text-indigo-500" />
            )}
          </div>
          <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${agentState.type === 'IDLE' ? 'bg-green-500' : agentState.type === 'ERROR' ? 'bg-red-500' : 'bg-indigo-500 animate-pulse'}`} />
            {agentState.type}
          </div>
          <div className="text-xs text-neutral-500 mt-2">
            {agentState.details}
          </div>
        </div>

        {/* Mock Artifact / Tool Execution */}
        <div className="border border-border rounded-xl bg-white dark:bg-neutral-900 overflow-hidden shadow-sm">
          <div className="flex items-center px-3 py-2 bg-neutral-50 dark:bg-neutral-800 border-b border-border text-xs font-medium text-neutral-600 dark:text-neutral-300">
            <Code2 size={14} className="mr-2" />
            Active Tools
          </div>
          <div className="p-4 text-xs font-mono text-neutral-500">
            {!agentState.activeTool ? (
              <span className="text-neutral-400">No tools currently executing.</span>
            ) : (
              <div className="flex flex-col gap-2 break-all">
                <div className="flex items-center gap-2">
                  <span className="text-indigo-500 shrink-0">❯</span> 
                  <span className="truncate">{agentState.activeTool.split('(')[0]}</span>
                </div>
                <div className="flex items-center gap-2 text-neutral-400 pl-4 text-[10px] leading-relaxed">
                  <span>{agentState.activeTool}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
