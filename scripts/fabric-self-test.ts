import fs from 'fs';
import os from 'os';
import path from 'path';
import { BrainkExecutionFabric } from '../fabric-runtime';

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

  const claimed = fabric.claim('self-test-worker', 5_000);
  if (!claimed || claimed.id !== first.id || claimed.state !== 'LEASED') {
    throw new Error('claim failed');
  }

  const beat = fabric.heartbeat(claimed.id, claimed.leaseId!, 'self-test-worker', 5_000);
  if (beat.state !== 'LEASED' || !beat.leaseUntil) throw new Error('heartbeat failed');

  const snapshot = fabric.snapshot();
  if (snapshot.jobs.length !== 1) throw new Error('unexpected job count');

  console.log(JSON.stringify({
    result: 'PASS',
    jobId: claimed.id,
    storeVersion: snapshot.version,
    state: snapshot.jobs[0].state,
    evidenceKinds: snapshot.jobs[0].evidence.map(e => e.kind)
  }));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
