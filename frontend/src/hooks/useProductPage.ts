import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchProducts, type ProductListItem } from '../api/products'

type PageState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; products: ProductListItem[]; nextCursor: string | null }

export interface UseProductPageResult {
  status: PageState['status']
  products: ProductListItem[]
  errorMessage: string | null
  isFirstPage: boolean
  hasNextPage: boolean
  goNext: () => void
  goPrev: () => void
}

/**
 * Cursor stack + fetch state for the products list page.
 *
 * "Previous" is a client-held stack of cursors already visited -- the API is
 * never asked to page backwards (see `specs/S8.md`). `pageIndex` indexes into
 * `cursorStack`, where `cursorStack[i]` is the cursor that produced page `i`
 * (`null` for the first page).
 */
export function useProductPage(): UseProductPageResult {
  const [state, setState] = useState<PageState>({ status: 'loading' })
  const [pageIndex, setPageIndex] = useState(0)
  const cursorStack = useRef<Array<string | null>>([null])

  const load = useCallback(async (cursor: string | null) => {
    setState({ status: 'loading' })
    try {
      const page = await fetchProducts(cursor)
      setState({
        status: 'success',
        products: page.products,
        nextCursor: page.nextCursor,
      })
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err)
      setState({ status: 'error', message: `Failed to load products: ${detail}` })
    }
  }, [])

  useEffect(() => {
    void load(cursorStack.current[pageIndex] ?? null)
  }, [pageIndex, load])

  const goNext = useCallback(() => {
    if (state.status !== 'success' || state.nextCursor === null) {
      return
    }
    const nextCursor = state.nextCursor
    setPageIndex((idx) => {
      const nextIndex = idx + 1
      cursorStack.current[nextIndex] = nextCursor
      return nextIndex
    })
  }, [state])

  const goPrev = useCallback(() => {
    setPageIndex((idx) => Math.max(0, idx - 1))
  }, [])

  const products = state.status === 'success' ? state.products : []
  const errorMessage = state.status === 'error' ? state.message : null
  const hasNextPage = state.status === 'success' && state.nextCursor !== null

  return {
    status: state.status,
    products,
    errorMessage,
    isFirstPage: pageIndex === 0,
    hasNextPage,
    goNext,
    goPrev,
  }
}
