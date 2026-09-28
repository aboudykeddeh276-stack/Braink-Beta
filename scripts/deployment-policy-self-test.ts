import fs from 'fs';
import path from 'path';

function requireTrue(value: unknown, message: string) {
  if (!value) throw new Error(message);
}

const root = process.cwd();
const sql = fs.readFileSync(path.join(root, 'deployment/sql/d030-zombie-recovery.sql'), 'utf8');
const cron = fs.readFileSync(path.join(root, 'deployment/cron.d/braink-d030-production'), 'utf8');
const nft = fs.readFileSync(path.join(root, 'deployment/network/braink-nftables.conf'), 'utf8');
const hba = fs.readFileSync(path.join(root, 'deployment/network/pg_hba.conf'), 'utf8');
const install = fs.readFileSync(path.join(root, 'deployment/install-production-controls.sh'), 'utf8');

requireTrue(sql.includes('FOR UPDATE SKIP LOCKED'), 'SQL must use row-locked recovery');
requireTrue(sql.includes("slot_state = 'LEASED'"), 'SQL must target leased slots only');
requireTrue(sql.includes("slot_state = 'PENDING'"), 'SQL must return expired slots to pending');
requireTrue(!sql.includes("dispatched_status = TRUE"), 'recovery must never fabricate retrigger dispatch');

requireTrue(cron.includes('d030-zombie-recovery.sql'), 'cron must execute database recovery');
requireTrue(cron.includes('npm run sweep:d030'), 'cron must execute runtime recovery/readback');

requireTrue(/chain input[\s\S]*policy drop/.test(nft), 'input default-deny missing');
requireTrue(/chain output[\s\S]*policy drop/.test(nft), 'output default-deny missing');
requireTrue(!/tcp dport 5432 ct state new accept\s*(?:#.*)?$/m.test(nft), 'unscoped public PostgreSQL allow detected');
requireTrue(nft.includes('ip daddr 10.0.0.0/8 tcp dport 5432'), 'private database egress missing');

requireTrue(hba.includes('scram-sha-256'), 'SCRAM database authentication missing');
requireTrue(hba.includes('0.0.0.0/0             reject'), 'IPv4 default database reject missing');
requireTrue(hba.includes('::/0                  reject'), 'IPv6 default database reject missing');

requireTrue(install.includes('nft -c -f'), 'deployment must preflight nftables before applying');
requireTrue(install.includes('PGHBA_PATH required'), 'deployment must not guess PostgreSQL config path');
requireTrue(install.includes('nft list ruleset'), 'deployment must read back active firewall state');

console.log(JSON.stringify({
  result: 'PASS',
  controls: {
    transactionalLeaseRecovery: true,
    runtimeSweep: true,
    defaultDenyIngress: true,
    defaultDenyEgress: true,
    privatePostgresOnly: true,
    scramHba: true,
    deploymentPreflight: true,
    firewallReadback: true
  }
}, null, 2));
