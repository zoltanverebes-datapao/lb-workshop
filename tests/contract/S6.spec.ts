/**
 * Contract tests for S6: Databricks App deployment configuration.
 *
 * No fixtures, no HTTP routes, no UI elements.
 * All tests verify file contents and permissions on disk using Node.js fs
 * and child_process.
 *
 * Files under test:
 *   - app.yaml  (project root)
 *   - scripts/start.sh  (project root/scripts/)
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { execSync, ExecSyncOptions } from 'child_process';

const ROOT = path.resolve(__dirname, '..', '..');
const APP_YAML = path.join(ROOT, 'app.yaml');
const START_SH = path.join(ROOT, 'scripts', 'start.sh');

/** Run a shell command; return { stdout, stderr, exitCode }. */
function run(
  cmd: string,
  cwd: string = ROOT,
): { stdout: string; stderr: string; exitCode: number } {
  const opts: ExecSyncOptions = {
    cwd,
    encoding: 'utf8',
    stdio: 'pipe',
  };
  try {
    const stdout = execSync(cmd, opts) as unknown as string;
    return { stdout: String(stdout), stderr: '', exitCode: 0 };
  } catch (err: unknown) {
    const e = err as { status?: number; stdout?: string; stderr?: string };
    return {
      stdout: String(e.stdout ?? ''),
      stderr: String(e.stderr ?? ''),
      exitCode: typeof e.status === 'number' ? e.status : 1,
    };
  }
}

// ---------------------------------------------------------------------------
// C1: app.yaml exists, is valid YAML, and command equals ['bash', 'scripts/start.sh']
// ---------------------------------------------------------------------------
test("C1: app.yaml exists at project root with correct command field", () => {
  expect(
    fs.existsSync(APP_YAML),
    `${APP_YAML} must exist`,
  ).toBe(true);

  // Validate YAML using python3 (available in test environment)
  const result = run(
    `python3 -c "import yaml, sys; d=yaml.safe_load(open('app.yaml')); assert d['command']==['bash','scripts/start.sh'], f'command is {d[\"command\"]}'; print('OK')"`,
    ROOT,
  );
  expect(
    result.exitCode,
    `app.yaml YAML parse or command assertion failed (exit ${result.exitCode}):\n${result.stdout}\n${result.stderr}`,
  ).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

// ---------------------------------------------------------------------------
// C2: scripts/start.sh exists and is executable
// ---------------------------------------------------------------------------
test('C2: scripts/start.sh exists and is executable', () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const result = run('test -x scripts/start.sh && echo OK', ROOT);
  expect(
    result.exitCode,
    `scripts/start.sh is not executable (exit ${result.exitCode})`,
  ).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

// ---------------------------------------------------------------------------
// C3: scripts/start.sh starts with #!/usr/bin/env bash shebang
// ---------------------------------------------------------------------------
test("C3: scripts/start.sh has #!/usr/bin/env bash shebang on first line", () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  const firstLine = content.split('\n')[0];
  expect(
    firstLine,
    `First line must be '#!/usr/bin/env bash', got: '${firstLine}'`,
  ).toBe('#!/usr/bin/env bash');
});

// ---------------------------------------------------------------------------
// C4: scripts/start.sh contains 'set -e'
// ---------------------------------------------------------------------------
test("C4: scripts/start.sh contains 'set -e' for fail-fast behaviour", () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    "scripts/start.sh must contain 'set -e'",
  ).toMatch(/\bset -e\b/);
});

// ---------------------------------------------------------------------------
// C5: scripts/start.sh installs frontend dependencies (npm install or npm ci)
// ---------------------------------------------------------------------------
test('C5: scripts/start.sh installs frontend dependencies with npm install or npm ci', () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    'scripts/start.sh must contain npm install or npm ci',
  ).toMatch(/npm\s+(install|ci)/);
});

// ---------------------------------------------------------------------------
// C6: scripts/start.sh builds the frontend (npm run build)
// ---------------------------------------------------------------------------
test("C6: scripts/start.sh builds the frontend with 'npm run build'", () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    "scripts/start.sh must contain 'npm run build'",
  ).toContain('npm run build');
});

// ---------------------------------------------------------------------------
// C7: scripts/start.sh installs backend dependencies (uv sync)
// ---------------------------------------------------------------------------
test("C7: scripts/start.sh installs backend dependencies with 'uv sync'", () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    "scripts/start.sh must contain 'uv sync'",
  ).toContain('uv sync');
});

// ---------------------------------------------------------------------------
// C8: scripts/start.sh starts uvicorn with app.main:app, --host 0.0.0.0,
//     and --port referencing DATABRICKS_APP_PORT (not a hardcoded number)
// ---------------------------------------------------------------------------
test('C8: scripts/start.sh starts uvicorn with correct app, host, and port variable', () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');

  expect(
    content,
    "scripts/start.sh must reference 'uvicorn app.main:app'",
  ).toMatch(/uvicorn\s+app\.main:app/);

  expect(
    content,
    "scripts/start.sh must contain '--host 0.0.0.0'",
  ).toContain('--host 0.0.0.0');

  expect(
    content,
    "scripts/start.sh must reference DATABRICKS_APP_PORT for --port",
  ).toContain('DATABRICKS_APP_PORT');
});

// ---------------------------------------------------------------------------
// C9: scripts/start.sh uses 'exec' for the final uvicorn command
// ---------------------------------------------------------------------------
test("C9: scripts/start.sh uses 'exec' for the final uvicorn command", () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    "scripts/start.sh must use 'exec ... uvicorn' so the server replaces the shell",
  ).toMatch(/exec\s+[^\n]*uvicorn/);
});

// ---------------------------------------------------------------------------
// C10: Reject — app.yaml must not contain secrets or connection strings
// ---------------------------------------------------------------------------
test('C10: app.yaml contains no hardcoded secrets, passwords, or connection strings', () => {
  expect(
    fs.existsSync(APP_YAML),
    `${APP_YAML} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(APP_YAML, 'utf8');
  expect(
    content,
    'app.yaml must not contain password, secret, postgres://, or DATABASE_URL',
  ).not.toMatch(/password|secret|postgres:\/\/|DATABASE_URL/i);
});

// ---------------------------------------------------------------------------
// C11: Reject — scripts/start.sh must not hardcode the server listen port number
// ---------------------------------------------------------------------------
test('C11: scripts/start.sh does not hardcode a port number for --port', () => {
  expect(
    fs.existsSync(START_SH),
    `${START_SH} must exist`,
  ).toBe(true);

  const content = fs.readFileSync(START_SH, 'utf8');
  expect(
    content,
    "scripts/start.sh must not contain '--port <number>' (port must come from DATABRICKS_APP_PORT)",
  ).not.toMatch(/--port\s+[0-9]+/);
});

// ---------------------------------------------------------------------------
// C12: app.yaml contains no 'env' block
// ---------------------------------------------------------------------------
test("C12: app.yaml contains no 'env' block (environment variables managed in Databricks UI)", () => {
  expect(
    fs.existsSync(APP_YAML),
    `${APP_YAML} must exist`,
  ).toBe(true);

  const result = run(
    `python3 -c "import yaml; d=yaml.safe_load(open('app.yaml')); assert 'env' not in d, 'env block found'; print('OK')"`,
    ROOT,
  );
  expect(
    result.exitCode,
    `app.yaml must not contain an 'env' block (exit ${result.exitCode}):\n${result.stdout}\n${result.stderr}`,
  ).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});
