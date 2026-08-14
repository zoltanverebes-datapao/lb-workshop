/**
 * Contract tests for S8: Product landing page with keyset-paginated product list.
 *
 * Drives both the HTTP API (`GET /api/products`, `/__test__/seed/*`) and the
 * rendered `/app` page at http://localhost:8100 (per playwright.config.ts
 * baseURL). A handful of criteria (C10-C13, C19-C22, C24-C25) are specified in
 * the spec's rubric as raw shell/pytest/vitest commands rather than
 * browser/API interactions; those are reproduced here as read-only
 * filesystem/subprocess checks so `-g "C<n>"` still selects a test for every
 * criterion, without writing outside `tests/contract/` and without the
 * self-referential recursion that a literal `bash scripts/verify.sh` call
 * from inside this file would cause (see the C25 comment below).
 */

import { test, expect, APIRequestContext } from '@playwright/test';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { execSync } from 'child_process';

const ROOT = path.resolve(__dirname, '..', '..');

// ---------------------------------------------------------------------------
// Shell helper (mirrors S6.spec.ts's `run`): never throws, returns exit code.
// ---------------------------------------------------------------------------
function run(cmd: string, cwd: string = ROOT): { stdout: string; stderr: string; exitCode: number } {
  try {
    const stdout = execSync(cmd, { cwd, encoding: 'utf8', stdio: 'pipe', shell: '/bin/bash' });
    return { stdout: String(stdout), stderr: '', exitCode: 0 };
  } catch (err: unknown) {
    const e = err as { status?: number | null; stdout?: string; stderr?: string };
    return {
      stdout: String(e.stdout ?? ''),
      stderr: String(e.stderr ?? ''),
      exitCode: typeof e.status === 'number' ? e.status : 1,
    };
  }
}

// ---------------------------------------------------------------------------
// Fixture helper: seeding a fixture *is* the reset (each seed route empties
// stock_levels then products before inserting its own rows -- there is no
// separate /__test__/reset route in this spec's interface contract).
// ---------------------------------------------------------------------------
async function seed(
  request: APIRequestContext,
  name: string,
): Promise<{ fixture: string; productIds: string[] }> {
  const res = await request.post(`/__test__/seed/products/${name}`);
  expect(res.status(), `seeding products/${name} must return 200`).toBe(200);
  return res.json();
}

// ===========================================================================
// C1-C9, C23: GET /api/products and /__test__/seed/* -- pure HTTP
// ===========================================================================

test('C1: first page of twenty-five is 10 items, ProductListItem has exactly 3 keys', async ({ request }) => {
  await seed(request, 'twenty-five');
  const res = await request.get('/api/products?limit=10');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body.products).toHaveLength(10);
  expect(body.products[0].name).toBe('Product 01');
  expect(typeof body.nextCursor).toBe('string');
  expect(body.nextCursor.length).toBeGreaterThan(0);
  for (const item of body.products) {
    expect(Object.keys(item).sort()).toEqual(['id', 'name', 'stockLevel']);
  }
});

test('C2: paging twenty-five with limit=10 takes exactly 3 requests (10,10,5) covering all seed ids in order', async ({ request }) => {
  const { productIds } = await seed(request, 'twenty-five');

  const counts: number[] = [];
  const seenIds: string[] = [];
  let cursor: string | null = null;
  let requests = 0;
  let nextCursor: string | null = null;

  while (requests < 10) {
    const url = cursor ? `/api/products?limit=10&cursor=${encodeURIComponent(cursor)}` : '/api/products?limit=10';
    const res = await request.get(url);
    expect(res.status()).toBe(200);
    const body = await res.json();
    counts.push(body.products.length);
    for (const item of body.products) seenIds.push(item.id);
    requests += 1;
    nextCursor = body.nextCursor;
    if (nextCursor === null) break;
    cursor = nextCursor;
  }

  expect(requests).toBe(3);
  expect(counts).toEqual([10, 10, 5]);
  expect(new Set(seenIds).size).toBe(25);
  expect(seenIds).toEqual(productIds);
  expect(nextCursor).toBeNull();
});

test('C3: paging ties (5 shared created_at) with limit=2 takes exactly 3 requests (2,2,1) covering all seed ids in order', async ({ request }) => {
  const { productIds } = await seed(request, 'ties');

  const counts: number[] = [];
  const seenIds: string[] = [];
  let cursor: string | null = null;
  let requests = 0;
  let nextCursor: string | null = null;

  while (requests < 10) {
    const url = cursor ? `/api/products?limit=2&cursor=${encodeURIComponent(cursor)}` : '/api/products?limit=2';
    const res = await request.get(url);
    expect(res.status()).toBe(200);
    const body = await res.json();
    counts.push(body.products.length);
    for (const item of body.products) seenIds.push(item.id);
    requests += 1;
    nextCursor = body.nextCursor;
    if (nextCursor === null) break;
    cursor = nextCursor;
  }

  expect(requests).toBe(3);
  expect(counts).toEqual([2, 2, 1]);
  expect(new Set(seenIds).size).toBe(5);
  expect(seenIds).toEqual(productIds);
  expect(nextCursor).toBeNull();
});

test('C4: Product 24 has stockLevel null, Product 25 has the most recent row (3 litre, not the older gram row)', async ({ request }) => {
  await seed(request, 'twenty-five');
  const res = await request.get('/api/products?limit=100');
  expect(res.status()).toBe(200);
  const body = await res.json();
  const p24 = body.products.find((p: { name: string }) => p.name === 'Product 24');
  const p25 = body.products.find((p: { name: string }) => p.name === 'Product 25');
  expect(p24, 'Product 24 must be present').toBeTruthy();
  expect(p25, 'Product 25 must be present').toBeTruthy();
  expect(p24.stockLevel).toBeNull();
  expect(p25.stockLevel).toEqual({ quantity: 3, measure: 'litre' });
});

test('C5: empty fixture returns body deep-equal to {"products": [], "nextCursor": null}', async ({ request }) => {
  await seed(request, 'empty');
  const res = await request.get('/api/products');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body).toEqual({ products: [], nextCursor: null });
});

test('C6: limit=0, limit=101, limit=abc each reject with 422 {error, field: "limit"}', async ({ request }) => {
  await seed(request, 'empty');
  for (const limit of ['0', '101', 'abc']) {
    const res = await request.get(`/api/products?limit=${limit}`);
    expect(res.status(), `limit=${limit} must be 422`).toBe(422);
    const body = await res.json();
    expect(Object.keys(body).sort()).toEqual(['error', 'field']);
    expect(body.field).toBe('limit');
    expect(typeof body.error).toBe('string');
    expect(body.error.length).toBeGreaterThan(0);
  }
});

test('C7: cursor=not-a-cursor and cursor=Zm9v each reject with 422 field="cursor" (never 200, never 500)', async ({ request }) => {
  await seed(request, 'empty');
  for (const cursor of ['not-a-cursor', 'Zm9v']) {
    const res = await request.get(`/api/products?cursor=${cursor}`);
    expect(res.status(), `cursor=${cursor} must not be 200`).not.toBe(200);
    expect(res.status(), `cursor=${cursor} must not be 500`).not.toBe(500);
    expect(res.status()).toBe(422);
    const body = await res.json();
    expect(body.field).toBe('cursor');
  }
});

test('C8: unknown query params (sort, order, offset, q, page) are ignored -- body is byte-identical to limit=10 alone', async ({ request }) => {
  await seed(request, 'twenty-five');
  const plain = await request.get('/api/products?limit=10');
  const withExtras = await request.get('/api/products?limit=10&sort=name&order=desc&offset=5&q=Product&page=3');
  expect(plain.status()).toBe(200);
  expect(withExtras.status()).toBe(200);
  expect(await withExtras.text()).toBe(await plain.text());
});

test('C9: cursor= (empty string) behaves like an absent cursor; a previously-valid cursor replayed against emptied data returns 200 with an empty page (not 404, not 422)', async ({ request }) => {
  await seed(request, 'twenty-five');
  const bare = await request.get('/api/products?limit=10');
  const withEmptyCursor = await request.get('/api/products?limit=10&cursor=');
  expect(withEmptyCursor.status()).toBe(200);
  expect(await withEmptyCursor.text()).toBe(await bare.text());

  // Walk pages, remembering the last non-null nextCursor returned by the API
  // (an opaque value we only ever got from a real response -- never
  // constructed by the test).
  let cursor: string | null = null;
  let lastNonNullCursor: string | null = null;
  for (let i = 0; i < 5; i++) {
    const url = cursor ? `/api/products?limit=10&cursor=${encodeURIComponent(cursor)}` : '/api/products?limit=10';
    const res = await request.get(url);
    const body = await res.json();
    if (body.nextCursor === null) break;
    lastNonNullCursor = body.nextCursor;
    cursor = body.nextCursor;
  }
  expect(lastNonNullCursor, 'expected at least one non-null nextCursor while paging twenty-five').not.toBeNull();

  // Empty the table out from under that still-opaque cursor: it now points
  // past every remaining row, which the interface contract requires to be a
  // 200 empty page, not a 404.
  await seed(request, 'empty');
  const replay = await request.get(`/api/products?limit=10&cursor=${encodeURIComponent(lastNonNullCursor as string)}`);
  expect(replay.status()).toBe(200);
  expect(await replay.json()).toEqual({ products: [], nextCursor: null });
});

test('C23: seeding an unknown fixture name returns 404 (while a known fixture name still returns 200)', async ({ request }) => {
  // Anchor the negative case against a positive one in the same test: a bare
  // 404 here would also happen (for the wrong reason) if /__test__/* were not
  // mounted at all yet, so this only passes once known-vs-unknown fixture
  // names are genuinely distinguished.
  const known = await request.post('/__test__/seed/products/empty');
  expect(known.status(), 'a known fixture name must still seed successfully').toBe(200);

  const res = await request.post('/__test__/seed/products/no-such-fixture');
  expect(res.status()).toBe(404);
});

// ===========================================================================
// C14-C18: /app UI
// ===========================================================================

test('C14: /app renders product-table with 10 rows; first row is Product 01 with correct id and stock', async ({ page, request }) => {
  const { productIds } = await seed(request, 'twenty-five');
  await page.goto('/app');

  const table = page.getByRole('table', { name: 'Products' });
  await expect(table).toBeVisible();
  await expect(page.getByTestId('product-row')).toHaveCount(10);

  const firstRow = page.getByTestId('product-row').first();
  await expect(firstRow.getByTestId('product-name-cell')).toHaveText('Product 01');
  await expect(firstRow.getByTestId('product-id-cell')).toHaveText(productIds[0]);
  await expect(firstRow.getByTestId('product-stock-cell')).toHaveText('10 pieces');
});

test('C15: clicking Next replaces rows with Product 11-20, then Product 21-25 (5 rows), then Next is disabled', async ({ page, request }) => {
  await seed(request, 'twenty-five');
  await page.goto('/app');

  await expect(page.getByTestId('product-row')).toHaveCount(10);
  await page.getByRole('button', { name: 'Next page' }).click();

  await expect(page.getByTestId('product-row')).toHaveCount(10);
  await expect(page.getByTestId('product-row').first().getByTestId('product-name-cell')).toHaveText('Product 11');
  await expect(page.getByTestId('product-row').last().getByTestId('product-name-cell')).toHaveText('Product 20');

  await page.getByRole('button', { name: 'Next page' }).click();

  await expect(page.getByTestId('product-row')).toHaveCount(5);
  await expect(page.getByTestId('product-row').last().getByTestId('product-name-cell')).toHaveText('Product 25');
  await expect(page.getByRole('button', { name: 'Next page' })).toBeDisabled();
});

test('C16: Previous is disabled on page 1; Next then Previous returns to Product 01-10 with Previous disabled again', async ({ page, request }) => {
  await seed(request, 'twenty-five');
  await page.goto('/app');

  await expect(page.getByRole('button', { name: 'Previous page' })).toBeDisabled();

  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByTestId('product-row').first().getByTestId('product-name-cell')).toHaveText('Product 11');

  await page.getByRole('button', { name: 'Previous page' }).click();

  await expect(page.getByTestId('product-row')).toHaveCount(10);
  await expect(page.getByTestId('product-row').first().getByTestId('product-name-cell')).toHaveText('Product 01');
  await expect(page.getByRole('button', { name: 'Previous page' })).toBeDisabled();
});

test('C17: empty fixture shows product-empty with "No products"; table and page buttons are absent', async ({ page, request }) => {
  await seed(request, 'empty');
  await page.goto('/app');

  await expect(page.getByTestId('product-empty')).toBeVisible();
  await expect(page.getByTestId('product-empty')).toContainText('No products');
  await expect(page.getByTestId('product-table')).toHaveCount(0);
  await expect(page.getByTestId('product-next-page')).toHaveCount(0);
  await expect(page.getByTestId('product-prev-page')).toHaveCount(0);
});

test('C18: on page 3, Product 24 (no stock_levels row) renders the em dash — in its stock cell', async ({ page, request }) => {
  await seed(request, 'twenty-five');
  await page.goto('/app');

  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByTestId('product-row').first().getByTestId('product-name-cell')).toHaveText('Product 11');
  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByTestId('product-row')).toHaveCount(5);

  const rows = page.getByTestId('product-row');
  const count = await rows.count();
  let found = false;
  for (let i = 0; i < count; i++) {
    const row = rows.nth(i);
    const name = await row.getByTestId('product-name-cell').textContent();
    if (name === 'Product 24') {
      found = true;
      await expect(row.getByTestId('product-stock-cell')).toHaveText('—');
    }
  }
  expect(found, 'Product 24 must be present on page 3').toBe(true);
});

// ===========================================================================
// C10-C13, C19-C22, C24: static/read-only checks mirroring the spec's own
// "verified by" shell commands. All are read-only (grep, pytest, a scratch
// temp-file codegen diff) -- none writes outside a system temp directory.
// ===========================================================================

test('C10: the product read path (backend/app/repositories/product.py) contains no OFFSET and no COUNT(', () => {
  const routesFile = path.join(ROOT, 'backend/app/routes/products.py');
  expect(fs.existsSync(routesFile), `${routesFile} must exist (GET /api/products route)`).toBe(true);

  const repoFile = path.join(ROOT, 'backend/app/repositories/product.py');
  expect(fs.existsSync(repoFile), `${repoFile} must exist`).toBe(true);

  const result = run(`! grep -niE '\\boffset\\b|count[[:space:]]*\\(' backend/app/repositories/product.py && echo OK`);
  expect(result.exitCode, `unexpected OFFSET/COUNT( in product.py:\n${result.stdout}${result.stderr}`).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

test('C11: no N+1 -- routes/products.py never references StockLevelRepository, stock level comes from the products query', () => {
  const routesFile = path.join(ROOT, 'backend/app/routes/products.py');
  expect(fs.existsSync(routesFile), `${routesFile} must exist`).toBe(true);

  const repoFile = path.join(ROOT, 'backend/app/repositories/product.py');
  expect(fs.existsSync(repoFile), `${repoFile} must exist`).toBe(true);

  const result = run(
    `! grep -q 'StockLevelRepository' backend/app/routes/products.py && grep -qi 'stock_levels' backend/app/repositories/product.py && echo OK`,
  );
  expect(result.exitCode, `N+1 guard failed:\n${result.stdout}${result.stderr}`).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

test('C12: the keyset index and stock-level lookup index exist in the migrated database', () => {
  const testFile = path.join(ROOT, 'backend/tests/test_products.py');
  expect(fs.existsSync(testFile), `${testFile} must exist`).toBe(true);

  const result = run(
    `cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_s2 uv run pytest tests/test_products.py -q -k index`,
  );
  expect(result.exitCode, `index test failed:\n${result.stdout}${result.stderr}`).toBe(0);
});

test('C13: migration 0002 is reversible -- apply, roll back one, apply again', () => {
  const migrationFile = path.join(ROOT, 'backend/migrations/0002_product_pagination_indexes.py');
  expect(fs.existsSync(migrationFile), `${migrationFile} must exist`).toBe(true);

  const script = [
    'from yoyo import get_backend, read_migrations',
    "b = get_backend('postgresql+psycopg://postgres:postgres@localhost:5432/test_s2')",
    "m = read_migrations('migrations')",
    'with b.lock():',
    '    b.apply_migrations(b.to_apply(m))',
    '    b.rollback_migrations(b.to_rollback(m)[:1])',
    '    b.apply_migrations(b.to_apply(m))',
    "print('OK')",
  ].join('\n');
  const result = run(`cd backend && uv run python -c "${script.replace(/"/g, '\\"')}"`);
  expect(result.exitCode, `migration reversibility check failed:\n${result.stdout}${result.stderr}`).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

test('C19: ProductTable.tsx is built with TanStack Table (useReactTable, getCoreRowModel, flexRender, manualPagination)', () => {
  const file = path.join(ROOT, 'frontend/src/components/ProductTable.tsx');
  expect(fs.existsSync(file), `${file} must exist`).toBe(true);

  const result = run(
    `grep -q 'useReactTable' frontend/src/components/ProductTable.tsx && grep -q 'getCoreRowModel' frontend/src/components/ProductTable.tsx && grep -q 'flexRender' frontend/src/components/ProductTable.tsx && grep -q 'manualPagination' frontend/src/components/ProductTable.tsx && echo OK`,
  );
  expect(result.exitCode, `TanStack Table usage check failed:\n${result.stdout}${result.stderr}`).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

test('C20: Reject -- no absolute API host (localhost/127.0.0.1) is hard-coded in frontend source', () => {
  const result = run(`! grep -rEn 'https?://(localhost|127\\.0\\.0\\.1)' frontend/src/ && echo OK`);
  expect(result.exitCode, `hard-coded API host found:\n${result.stdout}${result.stderr}`).toBe(0);
  expect(result.stdout.trim()).toBe('OK');
});

test('C21: frontend/src/api/types.ts is the committed output of generating from this build\'s OpenAPI schema, and the schema has no __test__ path', () => {
  const typesFile = path.join(ROOT, 'frontend/src/api/types.ts');
  expect(fs.existsSync(typesFile), `${typesFile} must exist (generated from the OpenAPI schema)`).toBe(true);

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 's8-openapi-'));
  const schemaPath = path.join(tmpDir, 'openapi.json');
  const generatedTypesPath = path.join(tmpDir, 'types.ts');

  const genScript = [
    'import json',
    'from app.main import app',
    's = app.openapi()',
    "leaked = [p for p in s['paths'] if '__test__' in p]",
    "assert not leaked, f'test routes leaked into schema: {leaked}'",
    `open(${JSON.stringify(schemaPath)}, 'w').write(json.dumps(s))`,
  ].join('\n');
  const genResult = run(
    `cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_s2 uv run python -c "${genScript.replace(/"/g, '\\"')}"`,
  );
  expect(genResult.exitCode, `schema generation failed:\n${genResult.stdout}${genResult.stderr}`).toBe(0);
  expect(fs.existsSync(schemaPath), 'schema JSON was not written').toBe(true);

  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const testPaths = Object.keys(schema.paths ?? {}).filter((p) => p.includes('__test__'));
  expect(testPaths, `__test__ paths must not appear in the OpenAPI document: ${testPaths.join(', ')}`).toEqual([]);

  const genTypesResult = run(`cd frontend && npx openapi-typescript ${schemaPath} -o ${generatedTypesPath}`);
  expect(genTypesResult.exitCode, `openapi-typescript generation failed:\n${genTypesResult.stdout}${genTypesResult.stderr}`).toBe(0);
  expect(fs.existsSync(generatedTypesPath), 'generated types.ts was not written').toBe(true);

  const committed = fs.readFileSync(typesFile, 'utf8');
  const generated = fs.readFileSync(generatedTypesPath, 'utf8');
  expect(committed, 'frontend/src/api/types.ts is stale relative to the current OpenAPI schema').toBe(generated);
});

test('C22: /__test__/* is 404 with APP_ENV unset; app refuses to start against a non-localhost DATABASE_URL under APP_ENV=test', () => {
  const testFile = path.join(ROOT, 'backend/tests/test_guards.py');
  expect(fs.existsSync(testFile), `${testFile} must exist`).toBe(true);

  const result = run(`cd backend && uv run pytest tests/test_guards.py -q`);
  expect(result.exitCode, `guard tests failed:\n${result.stdout}${result.stderr}`).toBe(0);
});

test('C24: ProductTable.test.tsx renders a stubbed null-stockLevel row and asserts the em dash, with no real network call', () => {
  const testFile = path.join(ROOT, 'frontend/src/components/ProductTable.test.tsx');
  expect(fs.existsSync(testFile), `${testFile} must exist`).toBe(true);

  // Scope the run to this one file: `npx vitest run` with no path would
  // "succeed" trivially (exit 1 for zero matched files is what we get today,
  // but a full suite run risks passing green before this file exists if any
  // other component test happens to be present).
  const result = run(`cd frontend && npx vitest run src/components/ProductTable.test.tsx --reporter=dot`);
  expect(result.exitCode, `ProductTable.test.tsx failed or was not found:\n${result.stdout}${result.stderr}`).toBe(0);
});

// ---------------------------------------------------------------------------
// C25: "The full gate is green" (`bash scripts/verify.sh`) is the same
// standing criterion as rubric-base's S1, and scripts/verify.sh's own
// contract stage runs `npx playwright test`, which would re-load this very
// file -- a literal, unconditional `execSync('bash scripts/verify.sh')` here
// would recurse into itself every time the real gate is graded. Rather than
// guess at a recursion-guard protocol the spec never names (and risk a
// doubled- or unbounded-cost gate), this is verified structurally: the
// script exists, is executable, and still names every stage the gate
// depends on. The full run itself is (and must remain) graded by invoking
// `bash scripts/verify.sh` directly, once, from outside this suite.
// ---------------------------------------------------------------------------
test('C25: scripts/verify.sh exists, is executable, and still runs every gate stage', () => {
  const verifyScript = path.join(ROOT, 'scripts/verify.sh');
  expect(fs.existsSync(verifyScript), `${verifyScript} must exist`).toBe(true);

  const execResult = run(`test -x scripts/verify.sh && echo OK`);
  expect(execResult.exitCode, 'scripts/verify.sh must be executable').toBe(0);
  expect(execResult.stdout.trim()).toBe('OK');

  const content = fs.readFileSync(verifyScript, 'utf8');
  for (const stage of ['ruff check', 'mypy', 'pytest', 'tsc --noEmit', 'eslint', 'vitest run', 'npm run build', 'playwright test']) {
    expect(content, `scripts/verify.sh must still invoke: ${stage}`).toContain(stage);
  }
});
