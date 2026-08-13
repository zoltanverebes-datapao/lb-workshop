import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the app-root element containing "Lakebase"', () => {
    render(<App />)
    const root = screen.getByTestId('app-root')
    expect(root).toBeInTheDocument()
    expect(root).toHaveTextContent('Lakebase')
  })
})
