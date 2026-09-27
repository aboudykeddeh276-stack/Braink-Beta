import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { execFile } from 'child_process';
import util from 'util';

const execFileAsync = util.promisify(execFile);

export type FabricJobState =
  | 'QUEUED'
  | 'LEASED'
  | 'EXECUTING'
  | 'SUCCEEDED'
  | 'FAILED';

export type FabricActuator = 'workspace-lint' | 'workspace-build' | 'fabric-self-test';

export interface FabricDispatch {
  assignmentId: string;
  foundry: string;
  sector: string;
  actuator: FabricActuator;
  parentTicket?: string;
  maxAttempts?: number;
  retryPolicy?: 'NEVER' | 'IDEMPOTENT';
  metadata?: Record<string, unknown>;
}

export interface FabricEvidence {
  at: string;
  kind: string;
  digest?: string;
  exitCode?: number;
  stdout?: string;
  stderr?: string;
  detail?: Record<string, unknown>;
}

export interface FabricJob {
  id: string;
  assignmentId: string;
  foundry: string;
  sector: string;
  actuator: FabricActuator;
  parentTicket?: string;
  state: FabricJobState;
  attempt: number;
  maxAttempts: number;
  retryPolicy: 'NEVER' | 'IDEMPOTENT';
  workerId?: string;
  leaseId?: string;
  leaseUntil?: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
  evidence: FabricEvidence[];
}

interface FabricStore {
  version: number;
  jobs: FabricJob[];
}

const MAX_LEASE_MS = 300_000;
const MAX_OUTPUT = 64_000;

function sha256(input: string | Buffer) {
  return crypto.createHash('sha256').update(input).digest('hex');
}

function bounded(text: string | undefined) {
  if (!text) return '';
  return text.length <= MAX_OUTPUT ? text : text.slice(0, MAX_OUTPUT) + '\n...[TRUNCATED]';
}

export class BrainkExecutionFabric {
  private readonly storePath: string;

  constructor(storePath = path.resolve(process.cwd(), 'braink_fabric_state.json')) {
    this.storePath = storePath;
    this.ensureStore();
  }

  private ensureStore() {
    if (!fs.existsSync(this.storePath)) {
      this.writeStore({ version: 1, jobs: [] });
    }
  }

  private readStore(): FabricStore {
    this.ensureStore();
    const raw = fs.readFileSync(this.storePath, 'utf8');
    const parsed = JSON.parse(raw);
    if (!Number.isInteger(parsed.version) || !Array.isArray(parsed.jobs)) {
      throw new Error('FABRIC_STORE_INVALID');
    }
    return parsed;
  }

  private writeStore(store: FabricStore) {
    const dir = path.dirname(this.storePath);
    fs.mkdirSync(dir, { recursive: true });
    const tmp = this.storePath + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(store, null, 2));
    fs.renameSync(tmp, this.storePath);
  }

  private mutate<T>(fn: (store: FabricStore) => T): T {
    const store = this.readStore();
    this.recoverExpiredLeases(store);
    const result = fn(store);
    store.version += 1;
    this.writeStore(store);
    return result;
  }

  private recoverExpiredLeases(store: FabricStore) {
    const now = Date.now();
    for (const job of store.jobs) {
      if ((job.state === 'LEASED' || job.state === 'EXECUTING') && job.leaseUntil && job.leaseUntil <= now) {
        const retryable = job.retryPolicy === 'IDEMPOTENT' && job.attempt < job.maxAttempts;
        job.state = retryable ? 'QUEUED' : 'FAILED';
        job.evidence.push({
          at: new Date().toISOString(),
          kind: retryable ? 'LEASE_EXPIRED_REQUEUED' : 'LEASE_EXPIRED_FAILED',
          detail: { previousWorkerId: job.workerId, previousLeaseId: job.leaseId }
        });
        delete job.workerId;
        delete job.leaseId;
        delete job.leaseUntil;
        job.updatedAt = new Date().toISOString();
      }
    }
  }

  enqueue(input: FabricDispatch): FabricJob {
    if (!input.assignmentId || !input.foundry || !input.sector || !input.actuator) {
      throw new Error('FABRIC_DISPATCH_INVALID');
    }

    const id = 'fabric-' + sha256(JSON.stringify({
      assignmentId: input.assignmentId,
      foundry: input.foundry,
      sector: input.sector,
      actuator: input.actuator,
      parentTicket: input.parentTicket ?? null
    })).slice(0, 20);

    return this.mutate(store => {
      const existing = store.jobs.find(job => job.id === id);
      if (existing) return existing;

      const now = new Date().toISOString();
      const job: FabricJob = {
        id,
        assignmentId: input.assignmentId,
        foundry: input.foundry,
        sector: input.sector,
        actuator: input.actuator,
        parentTicket: input.parentTicket,
        state: 'QUEUED',
        attempt: 0,
        maxAttempts: Math.max(1, Math.min(input.maxAttempts ?? 3, 10)),
        retryPolicy: input.retryPolicy ?? 'IDEMPOTENT',
        createdAt: now,
        updatedAt: now,
        metadata: input.metadata ?? {},
        evidence: [{ at: now, kind: 'ENQUEUED' }]
      };
      store.jobs.push(job);
      return job;
    });
  }

  claim(workerId: string, leaseMs = MAX_LEASE_MS): FabricJob | null {
    if (!workerId) throw new Error('FABRIC_WORKER_REQUIRED');
    const boundedLease = Math.max(1_000, Math.min(leaseMs, MAX_LEASE_MS));

    return this.mutate(store => {
      const job = store.jobs.find(candidate => candidate.state === 'QUEUED');
      if (!job) return null;

      const now = Date.now();
      job.state = 'LEASED';
      job.attempt += 1;
      job.workerId = workerId;
      job.leaseId = crypto.randomUUID();
      job.leaseUntil = now + boundedLease;
      job.updatedAt = new Date(now).toISOString();
      job.evidence.push({
        at: job.updatedAt,
        kind: 'CLAIMED',
        detail: { workerId, leaseId: job.leaseId, leaseUntil: job.leaseUntil, attempt: job.attempt }
      });
      return job;
    });
  }

  heartbeat(jobId: string, leaseId: string, workerId: string, leaseMs = MAX_LEASE_MS): FabricJob {
    const boundedLease = Math.max(1_000, Math.min(leaseMs, MAX_LEASE_MS));
    return this.mutate(store => {
      const job = store.jobs.find(candidate => candidate.id === jobId);
      if (!job) throw new Error('FABRIC_JOB_NOT_FOUND');
      if (job.leaseId !== leaseId || job.workerId !== workerId || !['LEASED', 'EXECUTING'].includes(job.state)) {
        throw new Error('FABRIC_LIVE_OWNED_LEASE_REQUIRED');
      }
      job.leaseUntil = Date.now() + boundedLease;
      job.updatedAt = new Date().toISOString();
      job.evidence.push({ at: job.updatedAt, kind: 'HEARTBEAT', detail: { workerId, leaseUntil: job.leaseUntil } });
      return job;
    });
  }

  async execute(jobId: string, leaseId: string, workerId: string): Promise<FabricJob> {
    const claimed = this.mutate(store => {
      const job = store.jobs.find(candidate => candidate.id === jobId);
      if (!job) throw new Error('FABRIC_JOB_NOT_FOUND');
      if (job.leaseId !== leaseId || job.workerId !== workerId || job.state !== 'LEASED') {
        throw new Error('FABRIC_LIVE_OWNED_LEASE_REQUIRED');
      }
      job.state = 'EXECUTING';
      job.updatedAt = new Date().toISOString();
      job.evidence.push({ at: job.updatedAt, kind: 'EXECUTION_STARTED', detail: { actuator: job.actuator } });
      return { ...job };
    });

    const command = this.resolveActuator(claimed.actuator);
    let stdout = '';
    let stderr = '';
    let exitCode = 0;

    try {
      const result = await execFileAsync(command.bin, command.args, {
        cwd: process.cwd(),
        timeout: 180_000,
        maxBuffer: 5 * 1024 * 1024,
        env: process.env
      });
      stdout = bounded(result.stdout);
      stderr = bounded(result.stderr);
    } catch (error: any) {
      exitCode = typeof error.code === 'number' ? error.code : 1;
      stdout = bounded(error.stdout);
      stderr = bounded(error.stderr || error.message);
    }

    return this.mutate(store => {
      const job = store.jobs.find(candidate => candidate.id === jobId);
      if (!job) throw new Error('FABRIC_JOB_NOT_FOUND');
      if (job.leaseId !== leaseId || job.workerId !== workerId || job.state !== 'EXECUTING') {
        throw new Error('FABRIC_LIVE_OWNED_LEASE_REQUIRED');
      }

      const digest = sha256(JSON.stringify({ actuator: job.actuator, exitCode, stdout, stderr }));
      const success = exitCode === 0;
      const retryable = !success && job.retryPolicy === 'IDEMPOTENT' && job.attempt < job.maxAttempts;

      job.evidence.push({
        at: new Date().toISOString(),
        kind: success ? 'EXECUTION_SUCCEEDED' : 'EXECUTION_FAILED',
        digest,
        exitCode,
        stdout,
        stderr
      });
      job.state = success ? 'SUCCEEDED' : retryable ? 'QUEUED' : 'FAILED';
      job.updatedAt = new Date().toISOString();

      delete job.workerId;
      delete job.leaseId;
      delete job.leaseUntil;
      return job;
    });
  }

  snapshot() {
    const store = this.readStore();
    this.recoverExpiredLeases(store);
    this.writeStore(store);
    const counts = store.jobs.reduce<Record<string, number>>((acc, job) => {
      acc[job.state] = (acc[job.state] ?? 0) + 1;
      return acc;
    }, {});
    return { version: store.version, counts, jobs: store.jobs };
  }

  private resolveActuator(actuator: FabricActuator) {
    switch (actuator) {
      case 'workspace-lint':
        return { bin: 'npm', args: ['run', 'lint'] };
      case 'workspace-build':
        return { bin: 'npm', args: ['run', 'build'] };
      case 'fabric-self-test':
        return { bin: 'npm', args: ['run', 'test:fabric'] };
      default:
        throw new Error('FABRIC_ACTUATOR_NOT_BOUND');
    }
  }
}
