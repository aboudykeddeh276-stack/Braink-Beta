import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { uptime, NodeContinuityRecord } from './node-continuity';
import { BrainkExecutionFabric, FabricActuator } from './fabric-runtime';

export type TurnState =
  | 'T1_PLANNING'
  | 'T2_T5_CRITIQUE_PENDING'
  | 'T6_DETERMINATION_PENDING'
  | 'RETRIGGER_QUEUED'
  | 'EXECUTION_BOUND'
  | 'EVIDENCE_VERIFICATION'
  | 'COMPLETED_CYCLE';

export type CritiqueSlotState = 'PENDING' | 'LEASED' | 'COMMITTED' | 'ABANDONED';
export type Priority = 'ORDINARY' | 'HIGH' | 'SIGNIFICANT_M1';

export interface PlanningPayload {
  intendedActions: string;
  underlyingLogic: string;
  dependencies: string[];
  failureModes: string[];
  expectedEffects: string;
  acceptanceConditions: string;
  evidenceSupported: boolean;
}

export interface CritiqueSlot {
  slotIndex: 2 | 3 | 4 | 5;
  state: CritiqueSlotState;
  assignedWorkerId?: string;
  leaseExpiresAt?: number;
  additiveAnalysis?: string;
  evidencePayload?: string;
  committedAt?: string;
}

export interface Determination {
  determinationId: string;
  validity: string;
  epicAlignment: string;
  disagreements: string;
  amendments: string;
  nextAction: string;
  diversityState: 'VERIFIED_DIVERSE' | 'INSUFFICIENT_DIVERSITY';
  committedAt: string;
}

export interface RetriggerPacket {
  retriggerId: string;
  targetWorkerIdentity: string;
  workerStatusFallback: 'ORIGINAL_RESUME' | 'REPLACEMENT_ROUTED';
  acceptedAmendments: string;
  disputedFindings: string;
  dependencies: Record<string, unknown>;
  currentPriority: Priority;
  requiredAuthorityLevel: string;
  previousExecutionState: string;
  reentryAddress: 'FIC1_ENTRY_POINT' | 'M1_CORE_ENTRY';
  exactNextExecutableAction: string;
  dispatched: boolean;
  executionJobId?: string;
  createdAt: string;
}

export interface DemandTask {
  taskId: string;
  ticketLineageId: string;
  originatingWorkerId: string;
  serviceRole: string;
  currentTurnState: TurnState;
  priority: Priority;
  epicComplianceSignature: string;
  planning: PlanningPayload;
  critiques: CritiqueSlot[];
  determination?: Determination;
  retrigger?: RetriggerPacket;
  createdAt: string;
  updatedAt: string;
}

interface WorkerRegistryEntry {
  workerId: string;
  serviceRoles: string[];
  capabilities: string[];
  node: NodeContinuityRecord;
}

interface ControlStore {
  version: number;
  tasks: DemandTask[];
  workers: WorkerRegistryEntry[];
  events: Array<Record<string, unknown>>;
}

const MAX_CRITIQUE_LEASE_MS = 300_000;
const LOCK_STALE_MS = 30_000;

function iso() { return new Date().toISOString(); }
function id(prefix: string) { return `${prefix}-${crypto.randomUUID()}`; }
function clone<T>(v: T): T { return JSON.parse(JSON.stringify(v)); }

export class D030ControlLaw {
  private readonly storePath: string;
  private readonly lockPath: string;
  private readonly fabric: BrainkExecutionFabric;

  constructor(
    storePath = path.resolve(process.cwd(), 'd030_control_state.json'),
    fabric = new BrainkExecutionFabric()
  ) {
    this.storePath = storePath;
    this.lockPath = storePath + '.lock';
    this.fabric = fabric;
    this.ensureStore();
  }

  private ensureStore() {
    if (!fs.existsSync(this.storePath)) {
      this.writeStore({ version: 1, tasks: [], workers: [], events: [] });
    }
  }

  private readStore(): ControlStore {
    this.ensureStore();
    return JSON.parse(fs.readFileSync(this.storePath, 'utf8'));
  }

  private writeStore(store: ControlStore) {
    fs.mkdirSync(path.dirname(this.storePath), { recursive: true });
    const tmp = this.storePath + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(store, null, 2));
    fs.renameSync(tmp, this.storePath);
  }

  private withLock<T>(fn: (store: ControlStore) => T, recoverExpired = true): T {
    const started = Date.now();
    while (true) {
      try {
        const fd = fs.openSync(this.lockPath, 'wx');
        try {
          const store = this.readStore();
          if (recoverExpired) this.recoverExpiredCritiqueLeases(store);
          const result = fn(store);
          store.version += 1;
          this.writeStore(store);
          return result;
        } finally {
          fs.closeSync(fd);
          try { fs.unlinkSync(this.lockPath); } catch {}
        }
      } catch (error: any) {
        if (error?.code !== 'EEXIST') throw error;
        try {
          const stat = fs.statSync(this.lockPath);
          if (Date.now() - stat.mtimeMs > LOCK_STALE_MS) {
            fs.unlinkSync(this.lockPath);
            continue;
          }
        } catch {}
        if (Date.now() - started > 5_000) throw new Error('D030_LOCK_TIMEOUT');
      }
    }
  }

  private event(store: ControlStore, event: string, data: Record<string, unknown>) {
    store.events.push({ seq: store.events.length + 1, event, at: iso(), ...data });
  }

  registerWorker(entry: WorkerRegistryEntry) {
    return this.withLock(store => {
      const existing = store.workers.find(w => w.workerId === entry.workerId);
      if (existing) Object.assign(existing, clone(entry));
      else store.workers.push(clone(entry));
      this.event(store, 'WORKER_REGISTERED', {
        workerId: entry.workerId,
        uptime: uptime(entry.node),
        runtimeId: entry.node.runtimeIdentity?.runtimeId ?? null,
        meshId: entry.node.meshIdentity?.meshId ?? null
      });
      return clone(entry);
    });
  }

  createTask(args: {
    ticketLineageId: string;
    workerId: string;
    serviceRole: string;
    plan: PlanningPayload;
    epicSignature: string;
    priority?: Priority;
  }) {
    if (!args.plan.evidenceSupported) throw new Error('TASK_CLAIM_EVIDENCE_REQUIRED');
    for (const key of ['intendedActions','underlyingLogic','expectedEffects','acceptanceConditions'] as const) {
      if (!args.plan[key]?.trim()) throw new Error(`PLANNING_FIELD_REQUIRED:${key}`);
    }

    return this.withLock(store => {
      const task: DemandTask = {
        taskId: id('task'),
        ticketLineageId: args.ticketLineageId,
        originatingWorkerId: args.workerId,
        serviceRole: args.serviceRole,
        currentTurnState: 'T2_T5_CRITIQUE_PENDING',
        priority: args.priority ?? 'ORDINARY',
        epicComplianceSignature: args.epicSignature,
        planning: clone(args.plan),
        critiques: ([2,3,4,5] as const).map(slotIndex => ({ slotIndex, state: 'PENDING' })),
        createdAt: iso(),
        updatedAt: iso()
      };
      store.tasks.push(task);
      this.event(store, 'T1_PLAN_COMMITTED', { taskId: task.taskId, workerId: args.workerId });
      return clone(task);
    });
  }

  claimCritique(workerId: string, leaseMs = MAX_CRITIQUE_LEASE_MS): { taskId: string; slot: CritiqueSlot } | null {
    const bounded = Math.max(1_000, Math.min(leaseMs, MAX_CRITIQUE_LEASE_MS));
    return this.withLock(store => {
      const candidates = store.tasks
        .filter(t => t.currentTurnState === 'T2_T5_CRITIQUE_PENDING' && t.originatingWorkerId !== workerId)
        .sort((a,b) => {
          const weight = (p: Priority) => p === 'SIGNIFICANT_M1' ? 3 : p === 'HIGH' ? 2 : 1;
          return weight(b.priority) - weight(a.priority);
        });

      for (const task of candidates) {
        if (task.critiques.some(c => c.state === 'COMMITTED' && c.assignedWorkerId === workerId)) continue;
        const slot = task.critiques.find(c => c.state === 'PENDING');
        if (!slot) continue;
        slot.state = 'LEASED';
        slot.assignedWorkerId = workerId;
        slot.leaseExpiresAt = Date.now() + bounded;
        task.updatedAt = iso();
        this.event(store, 'CRITIQUE_CLAIMED', {
          taskId: task.taskId, slotIndex: slot.slotIndex, workerId, leaseExpiresAt: slot.leaseExpiresAt
        });
        return { taskId: task.taskId, slot: clone(slot) };
      }
      return null;
    });
  }

  commitCritique(taskId: string, slotIndex: number, workerId: string, analysis: string, evidence: string) {
    if (!analysis.trim() || !evidence.trim()) throw new Error('CRITIQUE_ANALYSIS_AND_EVIDENCE_REQUIRED');
    return this.withLock(store => {
      const task = store.tasks.find(t => t.taskId === taskId);
      if (!task) throw new Error('TASK_NOT_FOUND');
      const slot = task.critiques.find(c => c.slotIndex === slotIndex);
      if (!slot) throw new Error('CRITIQUE_SLOT_NOT_FOUND');
      if (slot.state !== 'LEASED' || slot.assignedWorkerId !== workerId || !slot.leaseExpiresAt || slot.leaseExpiresAt <= Date.now()) {
        throw new Error('LIVE_OWNED_CRITIQUE_LEASE_REQUIRED');
      }
      slot.state = 'COMMITTED';
      slot.additiveAnalysis = analysis;
      slot.evidencePayload = evidence;
      slot.committedAt = iso();
      delete slot.leaseExpiresAt;
      task.updatedAt = iso();
      this.event(store, 'CRITIQUE_COMMITTED', { taskId, slotIndex, workerId });
      if (task.critiques.every(c => c.state === 'COMMITTED')) {
        task.currentTurnState = 'T6_DETERMINATION_PENDING';
        this.event(store, 'T6_ELIGIBLE', { taskId });
      }
      return clone(task);
    });
  }

  determine(taskId: string, actorId: string, payload: {
    validity: string;
    epicAlignment: string;
    disagreements: string;
    amendments: string;
    nextAction: string;
    dependencies?: Record<string, unknown>;
  }) {
    return this.withLock(store => {
      const task = store.tasks.find(t => t.taskId === taskId);
      if (!task) throw new Error('TASK_NOT_FOUND');
      if (task.currentTurnState !== 'T6_DETERMINATION_PENDING') throw new Error('T6_NOT_ELIGIBLE');
      const committed = task.critiques.filter(c => c.state === 'COMMITTED');
      if (committed.length !== 4) throw new Error('FOUR_COMMITTED_CRITIQUES_REQUIRED');
      const distinct = new Set(committed.map(c => c.assignedWorkerId));
      const diversityState = distinct.size === 4 ? 'VERIFIED_DIVERSE' : 'INSUFFICIENT_DIVERSITY';

      const determination: Determination = {
        determinationId: id('det'),
        validity: payload.validity,
        epicAlignment: payload.epicAlignment,
        disagreements: payload.disagreements,
        amendments: payload.amendments,
        nextAction: payload.nextAction,
        diversityState,
        committedAt: iso()
      };
      task.determination = determination;

      const target = this.resolveResumeWorker(store, task);
      task.retrigger = {
        retriggerId: id('retrigger'),
        targetWorkerIdentity: target.workerId,
        workerStatusFallback: target.workerId === task.originatingWorkerId ? 'ORIGINAL_RESUME' : 'REPLACEMENT_ROUTED',
        acceptedAmendments: payload.amendments,
        disputedFindings: payload.disagreements,
        dependencies: payload.dependencies ?? {},
        currentPriority: task.priority,
        requiredAuthorityLevel: task.serviceRole,
        previousExecutionState: 'TURN_6_DETERMINATION_COMPLETE',
        reentryAddress: task.priority === 'ORDINARY' ? 'FIC1_ENTRY_POINT' : 'M1_CORE_ENTRY',
        exactNextExecutableAction: payload.nextAction,
        dispatched: false,
        createdAt: iso()
      };
      task.currentTurnState = 'RETRIGGER_QUEUED';
      task.updatedAt = iso();
      this.event(store, 'T6_DETERMINED', {
        taskId, actorId, determinationId: determination.determinationId,
        diversityState, targetWorkerId: target.workerId
      });
      return clone(task);
    });
  }

  dispatchRetrigger(taskId: string, actuator: FabricActuator = 'workspace-build') {
    return this.withLock(store => {
      const task = store.tasks.find(t => t.taskId === taskId);
      if (!task || !task.retrigger) throw new Error('RETRIGGER_NOT_FOUND');
      if (task.currentTurnState !== 'RETRIGGER_QUEUED') throw new Error('RETRIGGER_NOT_ELIGIBLE');

      const target = store.workers.find(w => w.workerId === task.retrigger!.targetWorkerIdentity);
      if (!target || !uptime(target.node)) throw new Error('TARGET_NODE_NOT_UP');
      if (!target.capabilities.includes(actuator) && !target.capabilities.includes('software-evolution')) {
        throw new Error('TARGET_WORKER_ACTUATOR_NOT_AUTHORIZED');
      }

      const job = this.fabric.enqueue({
        assignmentId: `D030:${task.taskId}`,
        foundry: target.serviceRoles[0] ?? task.serviceRole,
        sector: 'Developer tools',
        actuator,
        parentTicket: task.ticketLineageId,
        maxAttempts: 3,
        retryPolicy: 'IDEMPOTENT',
        metadata: {
          retriggerId: task.retrigger.retriggerId,
          reentryAddress: task.retrigger.reentryAddress,
          nextAction: task.retrigger.exactNextExecutableAction
        }
      });
      task.retrigger.dispatched = true;
      task.retrigger.executionJobId = job.id;
      task.currentTurnState = 'EXECUTION_BOUND';
      task.updatedAt = iso();
      this.event(store, 'RETRIGGER_DISPATCHED', { taskId, workerId: target.workerId, jobId: job.id });
      return { task: clone(task), job };
    });
  }

  sweepExpiredLeases() {
    return this.withLock(store => {
      const before = store.events.length;
      this.recoverExpiredCritiqueLeases(store);
      return { recoveredEvents: store.events.length - before, version: store.version + 1 };
    }, false);
  }

  snapshot() {
    return this.withLock(store => clone(store));
  }

  private recoverExpiredCritiqueLeases(store: ControlStore) {
    const now = Date.now();
    for (const task of store.tasks) {
      for (const slot of task.critiques) {
        if (slot.state === 'LEASED' && slot.leaseExpiresAt && slot.leaseExpiresAt <= now) {
          this.event(store, 'CRITIQUE_LEASE_EXPIRED', {
            taskId: task.taskId, slotIndex: slot.slotIndex, previousWorkerId: slot.assignedWorkerId ?? null
          });
          slot.state = 'PENDING';
          delete slot.assignedWorkerId;
          delete slot.leaseExpiresAt;
          task.updatedAt = iso();
        }
      }
    }
  }

  private resolveResumeWorker(store: ControlStore, task: DemandTask): WorkerRegistryEntry {
    const original = store.workers.find(w => w.workerId === task.originatingWorkerId);
    if (original && uptime(original.node)) return original;

    const replacement = store.workers.find(w =>
      w.workerId !== task.originatingWorkerId &&
      w.serviceRoles.includes(task.serviceRole) &&
      uptime(w.node)
    );
    if (!replacement) throw new Error('NO_UP_REPLACEMENT_WORKER');
    return replacement;
  }
}
