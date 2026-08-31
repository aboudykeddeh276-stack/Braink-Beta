import React, { useState, useEffect } from 'react';
import { MonitorPlay, Smartphone, Globe, Cpu, Loader2, Play, Square, X } from 'lucide-react';

interface Workload {
  id: string;
  type: string;
  name: string;
  status: 'booting' | 'running' | 'terminated';
  logs: string[];
}

export default function WorkloadOrchestrator() {
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkloads = async () => {
    try {
      const res = await fetch('/api/workloads');
      const data = await res.json();
      setWorkloads(data);
    } catch (e) {
      console.error('Failed to fetch workloads', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkloads();
    const interval = setInterval(fetchWorkloads, 2000);
    return () => clearInterval(interval);
  }, []);

  const stopWorkload = async (id: string) => {
    try {
      await fetch(`/api/workloads/${id}`, { method: 'DELETE' });
      fetchWorkloads();
    } catch (e) {
      console.error('Failed to stop workload', e);
    }
  };

  const getIcon = (type: string) => {
    switch(type) {
      case 'linux': return <MonitorPlay className="w-6 h-6 text-emerald-400" />;
      case 'android': return <Smartphone className="w-6 h-6 text-green-400" />;
      case 'browser': return <Globe className="w-6 h-6 text-blue-400" />;
      case 'llm': return <Cpu className="w-6 h-6 text-purple-400" />;
      default: return <MonitorPlay className="w-6 h-6 text-zinc-400" />;
    }
  };

  if (loading) {
    return <div className="p-8 flex items-center justify-center text-zinc-500"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading Orchestrator...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-zinc-900 rounded-lg overflow-hidden text-white">
      <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <h2 className="font-semibold">Hardware Abstraction Layer</h2>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {workloads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-center">
            <Cpu className="w-12 h-12 mb-4 opacity-50" />
            <p>No active workloads.</p>
            <p className="text-sm">Instruct BrainK to spin up a desktop, Android subsystem, or browser.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {workloads.map(wl => (
              <div key={wl.id} className="border border-zinc-800 bg-zinc-950 rounded-lg overflow-hidden flex flex-col">
                <div className="flex items-center justify-between p-3 border-b border-zinc-800 bg-zinc-900/50">
                  <div className="flex items-center gap-3">
                    {getIcon(wl.type)}
                    <div>
                      <h3 className="font-medium text-sm text-zinc-200">{wl.name}</h3>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className={`w-2 h-2 rounded-full ${wl.status === 'running' ? 'bg-green-500' : wl.status === 'booting' ? 'bg-amber-500 animate-pulse' : 'bg-red-500'}`}></span>
                        <span className="text-xs text-zinc-500 uppercase tracking-wider">{wl.status}</span>
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => stopWorkload(wl.id)}
                    className="p-1.5 hover:bg-red-500/20 text-zinc-400 hover:text-red-400 rounded transition-colors"
                    title="Terminate"
                  >
                    <Square className="w-4 h-4 fill-current" />
                  </button>
                </div>
                <div className="flex-1 p-3 bg-black/50 font-mono text-xs overflow-y-auto h-48">
                  {wl.status === 'booting' && (
                    <div className="text-amber-400/80 mb-2 flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin" /> Initializing kernel and drivers...
                    </div>
                  )}
                  {wl.status === 'running' && wl.type === 'browser' && (
                    <div className="flex flex-col h-full items-center justify-center border border-zinc-800 rounded bg-zinc-100 text-zinc-800">
                      <Globe className="w-10 h-10 mb-2 text-zinc-300" />
                      <p className="text-zinc-500 text-sm">Headless Browser Session Active</p>
                      <p className="text-xs text-zinc-400">Waiting for remote CDP connection...</p>
                    </div>
                  )}
                  {wl.status === 'running' && wl.type !== 'browser' && (
                    <div className="text-green-400 space-y-1">
                      {wl.logs.map((log, i) => (
                        <div key={i}>{log}</div>
                      ))}
                      <div className="animate-pulse">_</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
