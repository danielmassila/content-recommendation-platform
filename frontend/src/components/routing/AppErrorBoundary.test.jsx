import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import AppErrorBoundary from './AppErrorBoundary'

const BrokenComponent = () => {
  throw new Error('render failed')
}

describe('AppErrorBoundary', () => {
  it('shows a recovery screen when a child crashes', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <AppErrorBoundary>
        <BrokenComponent />
      </AppErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Erreur inattendue')
    expect(screen.getByRole('button', { name: 'Retour à l’accueil' })).toBeInTheDocument()
  })
})
