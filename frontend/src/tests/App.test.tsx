import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from '../App'

// Mock the CSS module imports to prevent parsing errors in jsdom
vi.mock('../index.css', () => ({}))
vi.mock('../App.css', () => ({}))

// Ensure the local supabase wrapper object doesn't actually hit the network
vi.mock('../lib/supabase', () => ({
  supabase: {
    from: vi.fn(),
    auth: {
      getSession: vi.fn()
    }
  }
}))

describe('App', () => {
  it('renders the initial Agentic Speech scaffold', () => {
    render(<App />)
    
    // We expect basic UI mounting to exist showing our title text
    expect(screen.getByText(/Agentic Speech /i)).toBeInTheDocument()
  })
})
