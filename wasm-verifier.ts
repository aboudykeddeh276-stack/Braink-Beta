import crypto from 'crypto';

export interface WasmExecutionEvidence {
  moduleSha256: string;
  exportName: string;
  args: number[];
  result: unknown;
  startedAt: string;
  finishedAt: string;
  durationMs: number;
  evidenceSha256: string;
}

function sha256(data: Uint8Array | string) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

export async function executeVerificationWasm(
  bytes: Uint8Array,
  exportName: string,
  args: number[] = []
): Promise<WasmExecutionEvidence> {
  if (!bytes?.byteLength) throw new Error('WASM_MODULE_REQUIRED');
  if (!exportName?.trim()) throw new Error('WASM_EXPORT_REQUIRED');

  const module = await WebAssembly.compile(bytes);
  const imports = WebAssembly.Module.imports(module);
  if (imports.length) {
    throw new Error('WASM_IMPORTS_NOT_ALLOWED:' + imports.map(i => `${i.module}.${i.name}`).join(','));
  }

  const instance = await WebAssembly.instantiate(module, {});
  const fn = (instance.exports as Record<string, unknown>)[exportName];
  if (typeof fn !== 'function') throw new Error(`WASM_EXPORT_NOT_CALLABLE:${exportName}`);

  const started = Date.now();
  const startedAt = new Date(started).toISOString();
  const result = (fn as (...xs: number[]) => unknown)(...args);
  const finished = Date.now();
  const finishedAt = new Date(finished).toISOString();

  const moduleSha256 = sha256(bytes);
  const body = {
    moduleSha256,
    exportName,
    args,
    result: typeof result === 'bigint' ? result.toString() : result,
    startedAt,
    finishedAt,
    durationMs: finished - started
  };

  return {
    ...body,
    evidenceSha256: sha256(JSON.stringify(body))
  };
}
