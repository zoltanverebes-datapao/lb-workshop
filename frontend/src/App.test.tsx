import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'
import { stubFetch } from './setupTests'

describe('App', () => {
  it('renders the app-root element containing "Lakebase"', async () => {
    stubFetch({ products: [], nextCursor: null })
    render(<App />)
    const root = screen.getByTestId('app-root')
    expect(root).toBeInTheDocument()
    expect(root).toHaveTextContent('Lakebase')
    expect(await screen.findByTestId('product-empty')).toBeInTheDocument()
  })

  it('renders a "Products" heading', async () => {
    stubFetch({ products: [], nextCursor: null })
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Products', level: 2 })).toBeInTheDocument()
    await screen.findByTestId('product-empty')
  })
})
