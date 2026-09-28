import crypto from 'crypto';

export const NODE_LIFECYCLE = [
  'SEED',
  'SERVER_LINEAGE_LAUNCH',
  'VFS_MOUNT',
  'COMPILE',
  'ASSEMBLE',
  'RUNTIME',
  'MESH_SUBSCRIPTION',
  'UPTIME'
] as const;

export type NodeLifecycleState = typeof NODE_LIFECYCLE[number];

export interface NodeIdentity {
  seedId: string;
  lineageCommitment: string;
}

export interface RuntimeIdentity {
  runtimeId: string;
  incarnation: number;
}

export interface MeshIdentity {
  meshId: string;
  registered: boolean;
  subscribed: boolean;
  supporting: boolean;
  heartbeatAt?: string;
}

export interface LineageState {
  provenance: unknown[];
  history: unknown[];
  evidence: unknown[];
  relations: unknown[];
  learnedState: Record<string, unknown>;
  priorTransitions: unknown[];
}

export interface MirrorState {
  observed: Record<string, unknown>;
  expected: Record<string, unknown>;
  pending: Record<string, unknown>;
  delta: Record<string, unknown>;
}

export interface NodeContinuityRecord {
  nodeIdentity: NodeIdentity;
  runtimeIdentity: RuntimeIdentity | null;
  meshIdentity: MeshIdentity | null;
  vfsRoot: string | null;
  lifecycleState: NodeLifecycleState;
  lineage: LineageState;
  mirror: MirrorState | null;
  ilLlmRegisterCommitment: string | null;
  stateProof: string | null;
}

const canonical = (value: unknown) => JSON.stringify(value, Object.keys(value as any).sort());
const sha256 = (value: unknown) => crypto.createHash('sha256').update(
  typeof value === 'string' ? value : JSON.stringify(value)
).digest('hex');

export function lineageRoot(lineage: LineageState): string {
  return sha256(lineage);
}

export function nodeIdentityDigest(identity: NodeIdentity): string {
  return sha256(identity);
}

export function assertSeedAligned(record: NodeContinuityRecord) {
  const root = lineageRoot(record.lineage);
  if (!record.ilLlmRegisterCommitment) throw new Error('ILLLM_REGISTER_COMMITMENT_REQUIRED');
  if (root !== record.nodeIdentity.lineageCommitment) throw new Error('NODE_LINEAGE_COMMITMENT_MISMATCH');
  if (root !== record.ilLlmRegisterCommitment) throw new Error('ILLLM_REGISTER_ALIGNMENT_MISMATCH');
  return root;
}

export function uptime(record: NodeContinuityRecord): boolean {
  const mesh = record.meshIdentity;
  return Boolean(
    record.runtimeIdentity &&
    mesh &&
    mesh.registered &&
    mesh.subscribed &&
    mesh.supporting
  );
}

export function reconcileMirror(
  lineage: LineageState,
  observed: Record<string, unknown>,
  expected: Record<string, unknown>,
  pending: Record<string, unknown> = {}
): MirrorState {
  const keys = new Set([...Object.keys(observed), ...Object.keys(expected), ...Object.keys(pending)]);
  const delta: Record<string, unknown> = {};
  for (const key of keys) {
    const o = observed[key];
    const e = expected[key];
    const p = pending[key];
    if (JSON.stringify(o) !== JSON.stringify(e) || p !== undefined) {
      delta[key] = { observed: o, expected: e, pending: p };
    }
  }
  return { observed, expected, pending, delta };
}

export function admitLearning(
  record: NodeContinuityRecord,
  acceptedLearning: Record<string, unknown>,
  evidence: unknown
): NodeContinuityRecord {
  if (!evidence) throw new Error('LEARNING_EVIDENCE_REQUIRED');
  const nextLineage: LineageState = {
    ...record.lineage,
    learnedState: { ...record.lineage.learnedState, ...acceptedLearning },
    evidence: [...record.lineage.evidence, evidence],
    history: [...record.lineage.history, {
      kind: 'LEARNING_ADMITTED',
      runtimeId: record.runtimeIdentity?.runtimeId ?? null,
      learnedKeys: Object.keys(acceptedLearning).sort()
    }]
  };
  const root = lineageRoot(nextLineage);
  return {
    ...record,
    lineage: nextLineage,
    mirror: null,
    nodeIdentity: { ...record.nodeIdentity, lineageCommitment: root },
    ilLlmRegisterCommitment: root,
    stateProof: sha256({ seedId: record.nodeIdentity.seedId, lineageRoot: root })
  };
}

export function advanceLifecycle(
  record: NodeContinuityRecord,
  target: NodeLifecycleState,
  evidence: Record<string, unknown>
): NodeContinuityRecord {
  const currentIndex = NODE_LIFECYCLE.indexOf(record.lifecycleState);
  const targetIndex = NODE_LIFECYCLE.indexOf(target);
  if (targetIndex !== currentIndex + 1) {
    throw new Error(`NODE_LIFECYCLE_SEQUENTIAL_REQUIRED:${record.lifecycleState}->${target}`);
  }
  if (!evidence || Object.keys(evidence).length === 0) {
    throw new Error('NODE_LIFECYCLE_EVIDENCE_REQUIRED');
  }

  if (target === 'VFS_MOUNT' && !evidence.vfsRoot) throw new Error('VFS_ROOT_READBACK_REQUIRED');
  if (target === 'RUNTIME' && !evidence.runtimeId) throw new Error('RUNTIME_ID_READBACK_REQUIRED');
  if (target === 'MESH_SUBSCRIPTION') {
    for (const field of ['meshId','registered','subscribed','supporting']) {
      if (evidence[field] === undefined) throw new Error(`MESH_EVIDENCE_REQUIRED:${field}`);
    }
  }
  if (target === 'UPTIME') {
    const prospective: NodeContinuityRecord = {
      ...record,
      lifecycleState: target,
      meshIdentity: evidence.meshIdentity as MeshIdentity ?? record.meshIdentity,
      runtimeIdentity: evidence.runtimeIdentity as RuntimeIdentity ?? record.runtimeIdentity
    };
    if (!uptime(prospective)) throw new Error('UPTIME_REQUIRES_REGISTERED_SUBSCRIBED_SUPPORTING_RUNTIME');
  }

  const next: NodeContinuityRecord = { ...record, lifecycleState: target };
  if (target === 'VFS_MOUNT') next.vfsRoot = String(evidence.vfsRoot);
  if (target === 'RUNTIME') {
    next.runtimeIdentity = {
      runtimeId: String(evidence.runtimeId),
      incarnation: Number(evidence.incarnation ?? ((record.runtimeIdentity?.incarnation ?? 0) + 1))
    };
  }
  if (target === 'MESH_SUBSCRIPTION') {
    next.meshIdentity = {
      meshId: String(evidence.meshId),
      registered: Boolean(evidence.registered),
      subscribed: Boolean(evidence.subscribed),
      supporting: Boolean(evidence.supporting),
      heartbeatAt: evidence.heartbeatAt ? String(evidence.heartbeatAt) : undefined
    };
  }
  return next;
}

export function rehydrateNode(
  durable: NodeContinuityRecord,
  runtimeId: string,
  meshId: string
): NodeContinuityRecord {
  assertSeedAligned(durable);
  if (!durable.vfsRoot) throw new Error('REHYDRATION_VFS_REQUIRED');

  const nextIncarnation = (durable.runtimeIdentity?.incarnation ?? 0) + 1;
  return {
    ...durable,
    lifecycleState: 'RUNTIME',
    runtimeIdentity: { runtimeId, incarnation: nextIncarnation },
    meshIdentity: {
      meshId,
      registered: false,
      subscribed: false,
      supporting: false
    },
    mirror: null,
    stateProof: sha256({
      seedId: durable.nodeIdentity.seedId,
      lineageCommitment: durable.nodeIdentity.lineageCommitment,
      runtimeId,
      incarnation: nextIncarnation,
      vfsRoot: durable.vfsRoot
    })
  };
}

export function createSeedNode(seedId: string, lineage: LineageState): NodeContinuityRecord {
  const commitment = lineageRoot(lineage);
  return {
    nodeIdentity: { seedId, lineageCommitment: commitment },
    runtimeIdentity: null,
    meshIdentity: null,
    vfsRoot: null,
    lifecycleState: 'SEED',
    lineage,
    mirror: null,
    ilLlmRegisterCommitment: commitment,
    stateProof: sha256({ seedId, lineageCommitment: commitment })
  };
}
