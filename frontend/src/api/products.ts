import type { components } from './types'

/** Page size sent explicitly as `?limit=10` on every request. */
export const PAGE_SIZE = 10

export type ProductListItem = components['schemas']['ProductListItem']
export type ProductsPage = components['schemas']['ProductsPage']

/**
 * Fetch one page of `GET /api/products`.
 *
 * `cursor` is an opaque string previously returned as `nextCursor` -- never
 * constructed by the caller. Throws on a non-2xx response so callers can
 * render the `product-error` state.
 */
export async function fetchProducts(cursor?: string | null): Promise<ProductsPage> {
  const params = new URLSearchParams({ limit: String(PAGE_SIZE) })
  if (cursor) {
    params.set('cursor', cursor)
  }

  const response = await fetch(`/api/products?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return (await response.json()) as ProductsPage
}
