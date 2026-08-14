import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ProductTable from './ProductTable'
import type { ProductListItem } from '../api/products'

const PRODUCTS: ProductListItem[] = [
  { id: 'p1', name: 'Widget', stockLevel: { quantity: 120, measure: 'kilogram' } },
  { id: 'p2', name: 'No Stock Item', stockLevel: null },
]

describe('ProductTable', () => {
  it('renders rows from a stubbed products array (no network call) and shows an em dash for a null stockLevel', () => {
    render(
      <ProductTable
        products={PRODUCTS}
        isFirstPage={true}
        hasNextPage={false}
        onNextPage={vi.fn()}
        onPrevPage={vi.fn()}
      />,
    )

    expect(screen.getByRole('table', { name: 'Products' })).toBeInTheDocument()
    const rows = screen.getAllByTestId('product-row')
    expect(rows).toHaveLength(2)

    expect(rows[0].querySelector('[data-testid="product-name-cell"]')).toHaveTextContent(
      'Widget',
    )
    expect(rows[0].querySelector('[data-testid="product-stock-cell"]')).toHaveTextContent(
      '120 kilogram',
    )

    expect(rows[1].querySelector('[data-testid="product-name-cell"]')).toHaveTextContent(
      'No Stock Item',
    )
    expect(rows[1].querySelector('[data-testid="product-stock-cell"]')).toHaveTextContent('—')
  })

  it('disables Previous on the first page and Next when there is no next page', () => {
    render(
      <ProductTable
        products={PRODUCTS}
        isFirstPage={true}
        hasNextPage={false}
        onNextPage={vi.fn()}
        onPrevPage={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled()
  })

  it('enables Next when hasNextPage is true and Previous when not on the first page', () => {
    render(
      <ProductTable
        products={PRODUCTS}
        isFirstPage={false}
        hasNextPage={true}
        onNextPage={vi.fn()}
        onPrevPage={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Previous page' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Next page' })).toBeEnabled()
  })
})
