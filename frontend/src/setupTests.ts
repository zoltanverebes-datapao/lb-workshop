import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'

/**
 * Install a `global.fetch` stub for the current test that resolves with
 * `body` as JSON. No component test in this repo performs a real network
 * call (see `docs/conventions.md`) -- this is the one seam every component
 * test uses instead.
 */
export function stubFetch(body: unknown, status = 200): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    }),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})
