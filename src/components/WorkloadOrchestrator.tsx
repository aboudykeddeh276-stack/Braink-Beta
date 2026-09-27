import React, { useEffect, useMemo, useState } from 'react';
import { Activity, CheckCircle2, Clock3, Cpu, Loader2, RefreshCw, ShieldCheck, XCircle } from 'lucide-react';

type FabricState = 'QUEUED' | 'LEASED' | 'EXECUTING' | 'SUCCEEDED' | 'FAILED';

interface FabricEvidence {
  at: string;
  kind: string;
  digest?: string;
  exitCode?: number;
  stdout?: string;
  stderr?: string;
}

interface FabricJob {
  id: string;
  assignmentId: string;
  foundry: string;
  sector: string;
  actuator: string;
  parentTicket?: string;
  state: FabricState;
  attempt: number;
  maxAttempts: number;
  workerId?: string;
  leaseUntil?: number;
  updatedAt: string;
  evidence: FabricEvidence[];
}

interface FabricSnapshot {
  version: number;
  counts: Record<string, number>;
  jobs: FabricJob[];
}

const stateIcon = (state: FabricState) => {
  if (state === 'SUCCEEDED') return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
  if (state === 'FAILED') return <XCircle className="w-4 h-4 text-red-400" />;
  if (state === 'EXECUTING') return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
  if (state === 'LEASED') return <ShieldCheck className="w-4 h-4 text-amber-400" />;
  return <Clock3 className="w-4 h-4 text-zinc-400" />;
};

export default function WorkloadOrchestrator() {
  const [snapshot, setSnapshot] = useState<FabricSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const res = await fetch('/api/fabric');
      if (!res.ok) throw new Error(`fabric read failed: ${res.status}`);
      setSnapshot(await res.json());
      setError(null);
    } catch (e: any) {
      setError(e.message || String(e));
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, []);

  const totals = useMemo(() => {
    if (!snapshot) return [];
    return ['QUEUED', 'LEASED', 'EXECUTING', 'SUCCEEDED', 'FAILED'].map(state => ({
      state,
      count: snapshot.counts[state] || 0
    }));
  }, [snapshot]);

  if (!snapshot && !error) {
    return <div className="p-8 flex items-center justify-center text-zinc-500"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading execution fabric...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-zinc-900 rounded-lg overflow-hidden text-white">
      <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="font-semibold">BrainK Execution Fabric</h2>
            <p className="text-xs text-zinc-500">Durable queue · bounded leases · real process evidence</p>
          </div>
        </div>
        <button onClick={refresh} className="p-2 rounded hover:bg-zinc-800 text-zinc-400" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {error && <div className="m-4 p-3 rounded border border-red-900 bg-red-950/30 text-sm text-red-300">{error}</div>}

      {snapshot && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 p-4 border-b border-zinc-800">
            {totals.map(item => (
              <div key={item.state} className="rounded border border-zinc-800 bg-zinc-950 p-3">
                <div className="text-[11px] text-zinc-500 tracking-wider">{item.state}</div>
                <div className="text-xl font-semibold mt-1">{item.count}</div>
              </div>
            ))}
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-3">
            {snapshot.jobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-center">
                <Activity className="w-10 h-10 mb-3 opacity-50" />
                <p>No fabric jobs have been dispatched.</p>
                <p className="text-sm">Jobs appear only after a real dispatch reaches the durable substrate.</p>
              </div>
            ) : snapshot.jobs.slice().reverse().map(job => {
              const latest = job.evidence[job.evidence.length - 1];
              return (
                <div key={job.id} className="border border-zinc-800 bg-zinc-950 rounded-lg p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        {stateIcon(job.state)}
                        <span className="font-mono text-sm text-zinc-200">{job.assignmentId}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">{job.state}</span>
                      </div>
                      <div className="mt-2 text-xs text-zinc-500">
                        {job.foundry} · {job.sector} · {job.actuator}
                      </div>
                      {job.parentTicket && <div className="mt-1 text-xs text-zinc-600">Parent: {job.parentTicket}</div>}
                    </div>
                    <div className="text-right text-xs text-zinc-500">
                      attempt {job.attempt}/{job.maxAttempts}
                      <div>fabric v{snapshot.version}</div>
                    </div>
                  </div>

                  {job.workerId && (
                    <div className="mt-3 text-xs text-amber-300/80">
                      lease owner {job.workerId}{job.leaseUntil ? ` · expires ${new Date(job.leaseUntil).toLocaleString()}` : ''}
                    </div>
                  )}

                  {latest && (
                    <div className="mt-3 rounded bg-black/40 border border-zinc-800 p-3 font-mono text-xs">
                      <div className="text-zinc-400">{latest.kind} · {new Date(latest.at).toLocaleString()}</div>
                      {typeof latest.exitCode === 'number' && <div className="mt-1">exit={latest.exitCode}</div>}
                      {latest.digest && <div className="mt-1 break-all text-zinc-600">sha256={latest.digest}</div>}
                      {latest.stdout && <pre className="mt-2 whitespace-pre-wrap text-emerald-300 max-h-40 overflow-auto">{latest.stdout}</pre>}
                      {latest.stderr && <pre className="mt-2 whitespace-pre-wrap text-red-300 max-h-40 overflow-auto">{latest.stderr}</pre>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
