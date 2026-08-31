import React, { useState, useEffect } from 'react';
import { Cpu, Activity, MemoryStick, Server, Clock } from 'lucide-react';

export default function ServerRoom() {
  const [stats, setStats] = useState<any>(null);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/system');
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div className="p-8 text-neutral-500">Initializing telemetry...</div>;

  const memUsage = Math.round(((stats.totalmem - stats.freemem) / stats.totalmem) * 100);
  const uptimeHours = Math.floor(stats.uptime / 3600);
  const uptimeMinutes = Math.floor((stats.uptime % 3600) / 60);

  return (
    <div className="flex-1 flex flex-col p-6 bg-white dark:bg-[#09090b] overflow-hidden overflow-y-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-500 flex items-center justify-center">
          <Server size={20} />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Server Room</h2>
          <p className="text-sm text-neutral-500">Live Host Telemetry & Resource Allocation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Core Specs */}
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-neutral-500 mb-4 font-semibold text-sm">
            <Cpu size={16} /> Compute Core
          </div>
          <div className="text-2xl font-mono mb-1">{stats.cpus[0]?.model || 'Generic Processor'}</div>
          <div className="text-sm text-neutral-500">{stats.cpus.length} Cores / {stats.platform} {stats.release}</div>
        </div>

        <div className="bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-neutral-500 mb-4 font-semibold text-sm">
            <Clock size={16} /> Uptime
          </div>
          <div className="text-2xl font-mono mb-1">{uptimeHours}h {uptimeMinutes}m</div>
          <div className="text-sm text-neutral-500">System uninterrupted</div>
        </div>

        {/* Memory */}
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl p-5 md:col-span-2">
          <div className="flex items-center gap-2 text-neutral-500 mb-4 font-semibold text-sm">
            <MemoryStick size={16} /> Memory Allocation
          </div>
          <div className="flex items-end justify-between mb-2">
            <div className="text-3xl font-mono">{memUsage}% Usage</div>
            <div className="text-sm text-neutral-500 font-mono">
              {Math.round((stats.totalmem - stats.freemem) / 1024 / 1024 / 1024 * 10) / 10}GB / {Math.round(stats.totalmem / 1024 / 1024 / 1024 * 10) / 10}GB
            </div>
          </div>
          <div className="w-full bg-neutral-200 dark:bg-neutral-800 rounded-full h-3 overflow-hidden">
            <div 
              className={`h-full ${memUsage > 80 ? 'bg-red-500' : memUsage > 60 ? 'bg-yellow-500' : 'bg-green-500'} transition-all duration-1000 ease-out`}
              style={{ width: `${memUsage}%` }}
            />
          </div>
          <div className="mt-6 flex flex-col gap-2 border-t border-border pt-4">
            <div className="flex justify-between text-sm">
              <span className="text-neutral-500">Node Heap Total</span>
              <span className="font-mono">{Math.round(stats.processMemory.heapTotal / 1024 / 1024)} MB</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-neutral-500">Node Heap Used</span>
              <span className="font-mono">{Math.round(stats.processMemory.heapUsed / 1024 / 1024)} MB</span>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
