import React, { useState, useEffect } from 'react';
import { BrainCircuit, Book, ShieldAlert } from 'lucide-react';

export default function BrainKEvolution() {
  const [data, setData] = useState<{ coreDirectives: string[], learnedFacts: string[] } | null>(null);

  useEffect(() => {
    fetch('/api/evolution')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) return <div className="p-8 text-neutral-500">Loading neural pathways...</div>;

  return (
    <div className="flex-1 flex flex-col p-6 bg-white dark:bg-[#09090b] overflow-hidden overflow-y-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center">
          <BrainCircuit size={20} />
        </div>
        <div>
          <h2 className="text-xl font-semibold">BrainK Evolution</h2>
          <p className="text-sm text-neutral-500">Persistent Agent Memory & Core Directives</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Core Directives */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-neutral-900 dark:text-neutral-100 font-semibold mb-2">
            <ShieldAlert size={18} className="text-purple-500" />
            Core Directives
          </div>
          <div className="text-sm text-neutral-500 mb-2">Rules the agent has synthesized about how to operate.</div>
          {data.coreDirectives.length === 0 ? (
             <div className="p-4 rounded-xl border border-dashed border-border text-center text-sm text-neutral-500">
               No custom directives established yet.
             </div>
          ) : (
             <div className="flex flex-col gap-2">
               {data.coreDirectives.map((directive, i) => (
                 <div key={i} className="p-4 bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl text-sm leading-relaxed shadow-sm">
                   {directive}
                 </div>
               ))}
             </div>
          )}
        </div>

        {/* Learned Facts */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-neutral-900 dark:text-neutral-100 font-semibold mb-2">
            <Book size={18} className="text-indigo-500" />
            Learned Facts
          </div>
          <div className="text-sm text-neutral-500 mb-2">Contextual information the agent is remembering across sessions.</div>
          {data.learnedFacts.length === 0 ? (
             <div className="p-4 rounded-xl border border-dashed border-border text-center text-sm text-neutral-500">
               No facts persisted yet. Ask the agent to remember something.
             </div>
          ) : (
             <div className="flex flex-col gap-2">
               {data.learnedFacts.map((fact, i) => (
                 <div key={i} className="p-4 bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl text-sm leading-relaxed shadow-sm">
                   {fact}
                 </div>
               ))}
             </div>
          )}
        </div>

      </div>
    </div>
  );
}
