import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../../hooks'
import AdminRoute from './AdminRoute'

vi.mock('../../hooks', () => ({ useAuth: vi.fn() }))

describe('AdminRoute', () => {
  beforeEach(() => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { role: 'USER' },
    })
  })

  it('redirects a standard user away from administration', () => {
    render(
      <MemoryRouter initialEntries={['/dev']}>
        <Routes>
          <Route path="/dev" element={<AdminRoute>Administration</AdminRoute>} />
          <Route path="/discover" element={<p>Catalogue</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Catalogue')).toBeInTheDocument()
    expect(screen.queryByText('Administration')).not.toBeInTheDocument()
  })
})
