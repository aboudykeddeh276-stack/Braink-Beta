import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

export const EXECUTION_MANDATE =
  'DO THE WORK. EXECUTE THE CODE. DEPLOY IT INTO THE SUBSTRATE. DEPLOY IT INTO THE SUBSTRATE. DEPLOY IT INTO THE RUNTIMES.';

export const FABRIC_STAGES = [
  'BUILD',
  'SKILLS',
  'SUBSKILLS',
  'WORKFLOWS',
  'STATES',
  'ACTUATORS',
  'SUBSTRATES',
  'RUNTIMES',
  'OBSERVERS',
  'VERIFIERS',
  'EVIDENCE',
  'GOVERNANCE',
  'OPTIMISATION',
  'REDEPLOYMENT'
] as const;

export type FabricStage = typeof FABRIC_STAGES[number];

interface CanonicalAssignment {
  workId: string;
  foundry: string;
  sector: string;
  ownerLane: string;
  requiredWork: string;
  delivery: string;
  researchBasis: string;
  sourceState: string;
  parentTicket: string;
}

export interface SkillOperation {
  id: string;
  workId: string;
  foundry: string;
  sector: string;
  stage: FabricStage;
  mandate: string;
  what: string;
  how: string;
  howIs: string;
  howOperates: string;
  actsOn: string;
  change: string;
  changeLocation: string;
  observer: string;
  verifier: string;
  evidence: string;
  nextStatePredicate: string;
  failureBehavior: string;
  recovery: string;
}

const digest = (value: unknown) =>
  crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');

function nextStage(stage: FabricStage): FabricStage | 'SUSTAINED_CONTINUATION' {
  const index = FABRIC_STAGES.indexOf(stage);
  return index === FABRIC_STAGES.length - 1 ? 'SUSTAINED_CONTINUATION' : FABRIC_STAGES[index + 1];
}

function operationFor(assignment: CanonicalAssignment, stage: FabricStage): SkillOperation {
  const next = nextStage(stage);
  const id = `skill-op://${assignment.workId.toLowerCase()}/${stage.toLowerCase()}`;

  return {
    id,
    workId: assignment.workId,
    foundry: assignment.foundry,
    sector: assignment.sector,
    stage,
    mandate: EXECUTION_MANDATE,
    what: `${stage} responsibility for ${assignment.requiredWork}`,
    how: `Use the existing ${assignment.foundry} ownership lane and canonical ${assignment.workId} work identity; execute only through a bound actuator appropriate to ${assignment.sector}; preserve prior evidence and sibling work.`,
    howIs: `A deterministic state transition in the existing BrainK/Keddeh work fabric, keyed by ${assignment.workId} and stage ${stage}.`,
    howOperates: `Read current canonical assignment and durable job state; acquire or validate bounded ownership where mutation is required; invoke the registered actuator; capture exit/effect/readback; persist evidence; advance only when the stage predicate is satisfied.`,
    actsOn: `work://${assignment.workId}; foundry://${assignment.foundry}; sector://${assignment.sector}; deliverable://${assignment.delivery}`,
    change: `${stage} produces a traceable delta for ${assignment.requiredWork}; no later state is inferred from invocation alone.`,
    changeLocation: `BrainK source/substrate/runtime owned by ${assignment.foundry} for ${assignment.sector}, with coordination evidence returned to the canonical workbook.`,
    observer: `observer://${assignment.workId.toLowerCase()}/${stage.toLowerCase()}`,
    verifier: `verifier://independent-model/${assignment.workId.toLowerCase()}/${stage.toLowerCase()}`,
    evidence: `Exact source revision, command/job identity, actuator result, post-state/readback, content digest where applicable, and user/system/service impact for ${stage}.`,
    nextStatePredicate: next === 'SUSTAINED_CONTINUATION'
      ? 'Independent evidence is retained, operational observation is satisfactory, and the next eligible assignment/redeployment cycle is selected.'
      : `All ${stage} evidence requirements are satisfied without state inference; transition to ${next} becomes eligible.`,
    failureBehavior: 'Preserve the failed result and prior valid state; do not report success; release/recover bounded ownership and continue unrelated eligible work.',
    recovery: 'Reconcile current state and evidence, repair the smallest failed dependency or actuator, retry only when idempotency/authority permits, then re-read the effect before progression.'
  };
}

export function compileCanonicalSkillFabric(
  manifestPath = path.resolve(process.cwd(), 'braink-swarm-manifest.json')
) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (manifest?.schema !== 'braink.swarm.manifest.v1' || !Array.isArray(manifest.assignments)) {
    throw new Error('SKILL_FABRIC_MANIFEST_INVALID');
  }

  const operations: SkillOperation[] = [];
  for (const assignment of manifest.assignments as CanonicalAssignment[]) {
    for (const stage of FABRIC_STAGES) {
      operations.push(operationFor(assignment, stage));
    }
  }

  const requiredFields: (keyof SkillOperation)[] = [
    'mandate','what','how','howIs','howOperates','actsOn','change','changeLocation',
    'observer','verifier','evidence','nextStatePredicate','failureBehavior','recovery'
  ];

  for (const operation of operations) {
    for (const field of requiredFields) {
      if (!String(operation[field] ?? '').trim()) {
        throw new Error(`SKILL_FABRIC_FIELD_MISSING:${operation.id}:${field}`);
      }
    }
    if (operation.mandate !== EXECUTION_MANDATE) {
      throw new Error(`SKILL_FABRIC_MANDATE_DRIFT:${operation.id}`);
    }
    if (operation.observer === operation.verifier) {
      throw new Error(`SKILL_FABRIC_SELF_VERIFICATION:${operation.id}`);
    }
  }

  const body = {
    schema: 'braink.recursive-skill-fabric.v1',
    sourceManifest: path.basename(manifestPath),
    mandate: EXECUTION_MANDATE,
    stageOrder: FABRIC_STAGES,
    canonicalAssignments: manifest.assignments.length,
    canonicalFoundries: manifest.foundryCount,
    operationCount: operations.length,
    operations
  };

  return { ...body, fabricDigest: digest(body) };
}
