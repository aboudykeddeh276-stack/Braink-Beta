import fs from 'fs';
import os from 'os';
import path from 'path';
import { D030ControlLaw } from '../d030-control-law';
import { BrainkExecutionFabric } from '../fabric-runtime';
import { createSeedNode, advanceLifecycle, uptime } from '../node-continuity';
import { executeVerificationWasm } from '../wasm-verifier';

function upNode(id: string) {
  let node = createSeedNode('seed://' + id, {
    provenance: [],
    history: [],
    evidence: [],
    relations: [],
    learnedState: {},
    priorTransitions: []
  });
  node = advanceLifecycle(node, 'SERVER_LINEAGE_LAUNCH', { launched: true });
  node = advanceLifecycle(node, 'VFS_MOUNT', { vfsRoot: '/vfs/' + id });
  node = advanceLifecycle(node, 'COMPILE', { compiler: 'tsx' });
  node = advanceLifecycle(node, 'ASSEMBLE', { artifact: 'braink-beta' });
  node = advanceLifecycle(node, 'RUNTIME', { runtimeId: 'runtime://' + id, incarnation: 1 });
  node = advanceLifecycle(node, 'MESH_SUBSCRIPTION', {
    meshId: 'mesh://main',
    registered: true,
    subscribed: true,
    supporting: true
  });
  node = advanceLifecycle(node, 'UPTIME', {
    meshIdentity: node.meshIdentity,
    runtimeIdentity: node.runtimeIdentity,
    participationReadback: true
  });
  return node;
}

async function main() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'braink-d030-test-'));
  const fabric = new BrainkExecutionFabric(path.join(dir, 'fabric.json'));
  const control = new D030ControlLaw(path.join(dir, 'control.json'), fabric);

  const origin = upNode('origin');
  origin.meshIdentity!.supporting = false;
  control.registerWorker({
    workerId: 'origin',
    serviceRoles: ['Server Foundry'],
    capabilities: ['software-evolution'],
    node: origin
  });
  control.registerWorker({
    workerId: 'replacement',
    serviceRoles: ['Server Foundry'],
    capabilities: ['software-evolution', 'workspace-build'],
    node: upNode('replacement')
  });

  for (const workerId of ['critic-a','critic-b','critic-c','critic-d']) {
    control.registerWorker({
      workerId,
      serviceRoles: ['Audit'],
      capabilities: ['audit'],
      node: upNode(workerId)
    });
  }

  const task = control.createTask({
    ticketLineageId: 'WT-BRAINK-BETA-20260928-001',
    workerId: 'origin',
    serviceRole: 'Server Foundry',
    priority: 'SIGNIFICANT_M1',
    epicSignature: 'D-030',
    plan: {
      intendedActions: 'execute software evolution',
      underlyingLogic: 'polygonal critique then retrigger',
      dependencies: [],
      failureModes: ['lease expiry'],
      expectedEffects: 'bound retrigger job',
      acceptanceConditions: '4 distinct critiques and live target',
      evidenceSupported: true
    }
  });

  control.claimCritique('critic-a', 1000);
  await new Promise(resolve => setTimeout(resolve, 1100));
  const sweep = control.sweepExpiredLeases();

  const reclaimed = control.claimCritique('critic-a', 5000);
  if (!reclaimed) throw new Error('expired critique not reclaimed');
  control.commitCritique(task.taskId, reclaimed.slot.slotIndex, 'critic-a', 'analysis-a', 'evidence-a');

  for (const workerId of ['critic-b','critic-c','critic-d']) {
    const claim = control.claimCritique(workerId, 5000);
    if (!claim) throw new Error('critique claim unavailable:' + workerId);
    control.commitCritique(task.taskId, claim.slot.slotIndex, workerId, 'analysis-' + workerId, 'evidence-' + workerId);
  }

  const determined = control.determine(task.taskId, 'orchestrator', {
    validity: 'valid',
    epicAlignment: 'aligned',
    disagreements: 'none',
    amendments: 'execute build',
    nextAction: 'workspace build',
    dependencies: {}
  });
  const dispatched = control.dispatchRetrigger(task.taskId, 'workspace-build');

  // Minimal import-free WASM module exporting add(i32,i32)->i32.
  const wasmBytes = Uint8Array.from([
    0,97,115,109,1,0,0,0,1,7,1,96,2,127,127,1,127,3,2,1,0,
    7,7,1,3,97,100,100,0,0,10,9,1,7,0,32,0,32,1,106,11
  ]);
  const wasm = await executeVerificationWasm(wasmBytes, 'add', [20,22]);
  const snapshot = control.snapshot();

  const result = {
    status: 'PASS',
    expiredLeaseRecovered: sweep.recoveredEvents > 0,
    fourDistinctCritics: new Set(snapshot.tasks[0].critiques.map(c => c.assignedWorkerId)).size === 4,
    turnState: snapshot.tasks[0].currentTurnState,
    originalNodeUptime: uptime(origin),
    retriggerTarget: determined.retrigger?.targetWorkerIdentity,
    replacementRouting: determined.retrigger?.workerStatusFallback,
    executionJobState: dispatched.job.state,
    executionJobId: dispatched.job.id,
    wasmResult: wasm.result,
    wasmEvidenceSha256: wasm.evidenceSha256
  };

  if (!result.expiredLeaseRecovered) throw new Error('lease recovery not observed');
  if (!result.fourDistinctCritics) throw new Error('critic diversity not enforced');
  if (result.turnState !== 'EXECUTION_BOUND') throw new Error('retrigger not execution-bound');
  if (result.originalNodeUptime !== false) throw new Error('down origin incorrectly considered up');
  if (result.retriggerTarget !== 'replacement' || result.replacementRouting !== 'REPLACEMENT_ROUTED') {
    throw new Error('replacement routing not observed');
  }
  if (result.executionJobState !== 'QUEUED') throw new Error('durable job not queued');
  if (result.wasmResult !== 42) throw new Error('WASM verifier failed');

  console.log(JSON.stringify(result, null, 2));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
