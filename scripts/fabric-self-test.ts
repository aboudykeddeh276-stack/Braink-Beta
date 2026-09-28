import fs from 'fs';
import os from 'os';
import path from 'path';
import { BrainkExecutionFabric } from '../fabric-runtime';
import { compileCanonicalSkillFabric, EXECUTION_MANDATE, FABRIC_STAGES } from '../skill-fabric';

async function main() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'braink-fabric-test-'));
  const storePath = path.join(dir, 'state.json');
  const fabric = new BrainkExecutionFabric(storePath);

  const first = fabric.enqueue({
    assignmentId: 'SELFTEST-001',
    foundry: 'Server Foundry',
    sector: 'Developer tools',
    actuator: 'workspace-lint',
    parentTicket: 'WT-BRAINK-BETA-20260928-001',
    maxAttempts: 3,
    retryPolicy: 'IDEMPOTENT'
  });

  const duplicate = fabric.enqueue({
    assignmentId: 'SELFTEST-001',
    foundry: 'Server Foundry',
    sector: 'Developer tools',
    actuator: 'workspace-lint',
    parentTicket: 'WT-BRAINK-BETA-20260928-001',
    maxAttempts: 3,
    retryPolicy: 'IDEMPOTENT'
  });

  if (first.id !== duplicate.id) throw new Error('idempotency failed');

  const claimed = fabric.claim('self-test-worker', 5_000, 'SELFTEST-001');
  if (!claimed || claimed.id !== first.id || claimed.state !== 'LEASED') {
    throw new Error('claim failed');
  }

  const beat = fabric.heartbeat(claimed.id, claimed.leaseId!, 'self-test-worker', 5_000);
  if (beat.state !== 'LEASED' || !beat.leaseUntil) throw new Error('heartbeat failed');

  const swarmStore = path.join(dir, 'swarm-state.json');
  const swarm = new BrainkExecutionFabric(swarmStore);
  const seed1 = swarm.seedCanonicalSwarm(path.resolve(process.cwd(), 'braink-swarm-manifest.json'));
  const seed2 = swarm.seedCanonicalSwarm(path.resolve(process.cwd(), 'braink-swarm-manifest.json'));
  const swarmSnapshot = swarm.snapshot();

  if (seed1.assignmentCount !== 72) throw new Error(`canonical assignment count mismatch: ${seed1.assignmentCount}`);
  if (seed1.foundryCount !== 18) throw new Error(`canonical foundry count mismatch: ${seed1.foundryCount}`);
  if (seed1.executableJobsSeeded !== 18) throw new Error(`developer-tool executable lane count mismatch: ${seed1.executableJobsSeeded}`);
  if (seed2.executableJobsSeeded !== 18) throw new Error('idempotent reseed return mismatch');
  if (swarmSnapshot.jobs.length !== 18) throw new Error(`idempotent reseed persisted duplicate jobs: ${swarmSnapshot.jobs.length}`);
  if (new Set(swarmSnapshot.jobs.map(job => job.foundry)).size !== 18) throw new Error('not all 18 foundries represented');
  if (!swarmSnapshot.jobs.every(job => job.sector === 'Developer tools' && job.actuator === 'workspace-build')) {
    throw new Error('unbound lane was incorrectly materialised');
  }

  const skillFabric = compileCanonicalSkillFabric(path.resolve(process.cwd(), 'braink-swarm-manifest.json'));
  if (skillFabric.canonicalAssignments !== 72) throw new Error('skill fabric assignment count mismatch');
  if (skillFabric.canonicalFoundries !== 18) throw new Error('skill fabric foundry count mismatch');
  if (skillFabric.stageOrder.length !== FABRIC_STAGES.length) throw new Error('skill fabric stage count mismatch');
  if (skillFabric.operationCount !== 72 * FABRIC_STAGES.length) throw new Error(`skill fabric operation count mismatch: ${skillFabric.operationCount}`);
  if (!skillFabric.operations.every(operation => operation.mandate === EXECUTION_MANDATE)) {
    throw new Error('skill fabric mandate drift');
  }
  if (!skillFabric.operations.every(operation => operation.observer !== operation.verifier)) {
    throw new Error('skill fabric self-verification');
  }

  const snapshot = fabric.snapshot();
  if (snapshot.jobs.length !== 1) throw new Error('unexpected single-job test count');

  console.log(JSON.stringify({
    result: 'PASS',
    leaseTest: {
      jobId: claimed.id,
      storeVersion: snapshot.version,
      state: snapshot.jobs[0].state,
      evidenceKinds: snapshot.jobs[0].evidence.map(e => e.kind)
    },
    swarmTest: {
      canonicalAssignments: seed1.assignmentCount,
      canonicalFoundries: seed1.foundryCount,
      executableJobs: swarmSnapshot.jobs.length,
      uniqueFoundries: new Set(swarmSnapshot.jobs.map(job => job.foundry)).size,
      idempotentReseed: seed2.executableJobsSeeded === 18 && swarmSnapshot.jobs.length === 18
    },
    skillFabricTest: {
      stages: skillFabric.stageOrder.length,
      operations: skillFabric.operationCount,
      expectedOperations: 72 * FABRIC_STAGES.length,
      mandateStable: skillFabric.operations.every(operation => operation.mandate === EXECUTION_MANDATE),
      independentVerifierRefs: skillFabric.operations.every(operation => operation.observer !== operation.verifier),
      digest: skillFabric.fabricDigest
    }
  }));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
