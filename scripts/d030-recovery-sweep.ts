import path from 'path';
import { D030ControlLaw } from '../d030-control-law';

const storePath = process.env.D030_CONTROL_STATE_PATH || path.resolve(process.cwd(), 'd030_control_state.json');
const control = new D030ControlLaw(storePath);
const result = control.sweepExpiredLeases();
process.stdout.write(JSON.stringify({ status: 'PASS', storePath, ...result }) + '\n');
