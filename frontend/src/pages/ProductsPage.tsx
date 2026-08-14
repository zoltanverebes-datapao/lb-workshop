import ProductTable from '../components/ProductTable'
import { useProductPage } from '../hooks/useProductPage'

/**
 * The product landing page: a keyset-paginated table of products. States are
 * mutually exclusive -- see `specs/S8.md`'s state table.
 */
export default function ProductsPage() {
  const { status, products, errorMessage, isFirstPage, hasNextPage, goNext, goPrev } =
    useProductPage()

  if (status === 'loading') {
    return <div data-testid="product-loading">Loading products…</div>
  }

  if (status === 'error') {
    return <div data-testid="product-error">{errorMessage}</div>
  }

  if (products.length === 0) {
    return <div data-testid="product-empty">No products</div>
  }

  return (
    <ProductTable
      products={products}
      isFirstPage={isFirstPage}
      hasNextPage={hasNextPage}
      onNextPage={goNext}
      onPrevPage={goPrev}
    />
  )
}
