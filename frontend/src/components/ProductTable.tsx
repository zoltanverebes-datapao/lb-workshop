import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import type { ProductListItem } from '../api/products'

const EM_DASH = '—'

const CELL_TEST_IDS: Record<string, string> = {
  id: 'product-id-cell',
  name: 'product-name-cell',
  stockLevel: 'product-stock-cell',
}

function formatStockLevel(stockLevel: ProductListItem['stockLevel']): string {
  if (stockLevel === null) {
    return EM_DASH
  }
  return `${stockLevel.quantity} ${stockLevel.measure}`
}

const columnHelper = createColumnHelper<ProductListItem>()

const columns = [
  columnHelper.accessor('id', {
    id: 'id',
    header: 'ID',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('name', {
    id: 'name',
    header: 'Name',
    cell: (info) => info.getValue(),
  }),
  columnHelper.display({
    id: 'stockLevel',
    header: 'Stock level',
    cell: (info) => formatStockLevel(info.row.original.stockLevel),
  }),
]

export interface ProductTableProps {
  products: ProductListItem[]
  isFirstPage: boolean
  hasNextPage: boolean
  onNextPage: () => void
  onPrevPage: () => void
}

/**
 * Renders the product list as a TanStack Table with Previous/Next controls.
 * Pagination is fully manual (`manualPagination: true`): the table instance
 * never slices `products` itself -- the API already returned one page.
 */
export default function ProductTable({
  products,
  isFirstPage,
  hasNextPage,
  onNextPage,
  onPrevPage,
}: ProductTableProps) {
  const table = useReactTable({
    data: products,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
  })

  return (
    <>
      <table aria-label="Products" data-testid="product-table">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} data-testid="product-row">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} data-testid={CELL_TEST_IDS[cell.column.id]}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <button data-testid="product-prev-page" onClick={onPrevPage} disabled={isFirstPage}>
        Previous page
      </button>
      <button data-testid="product-next-page" onClick={onNextPage} disabled={!hasNextPage}>
        Next page
      </button>
    </>
  )
}
