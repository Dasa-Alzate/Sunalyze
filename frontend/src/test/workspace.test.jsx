import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

const api = {
  workspace: {
    list: vi.fn(),
    switch: vi.fn(() => Promise.resolve({ ok: true, org_id: 2, role: 'member' })),
  },
}

vi.mock('@/api/client', () => ({ api, ApiError: class ApiError extends Error {} }))
vi.mock('@/services/toast', () => ({ toast: vi.fn() }))

let WorkspaceSwitcher

beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: WorkspaceSwitcher } = await import('@/app/WorkspaceSwitcher'))
})

const twoWorkspaces = {
  workspaces: [
    { org_id: 1, nombre: 'Org A', type: 'BUSINESS', role: 'owner', active: true },
    { org_id: 2, nombre: 'Org B', type: 'BUSINESS', role: 'member', active: false },
  ],
}

describe('WorkspaceSwitcher', () => {
  it('renders nothing for a single-workspace user', async () => {
    api.workspace.list.mockResolvedValueOnce({
      workspaces: [{ org_id: 1, nombre: 'Org A', type: 'PERSONAL', role: 'owner', active: true }],
    })
    const { container } = render(<WorkspaceSwitcher />)
    await waitFor(() => expect(api.workspace.list).toHaveBeenCalled())
    expect(container.querySelector('select')).toBeNull()
  })

  it('renders a select with all workspaces and the active one selected', async () => {
    api.workspace.list.mockResolvedValueOnce(twoWorkspaces)
    render(<WorkspaceSwitcher />)
    const select = await screen.findByRole('combobox')
    expect(select).toHaveValue('1')
    expect(screen.getByRole('option', { name: 'Org A' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Org B' })).toBeInTheDocument()
  })

  it('calls the switch endpoint and the refresh callback on change', async () => {
    api.workspace.list.mockResolvedValueOnce(twoWorkspaces)
    const onSwitched = vi.fn()
    render(<WorkspaceSwitcher onSwitched={onSwitched} />)
    const select = await screen.findByRole('combobox')
    fireEvent.change(select, { target: { value: '2' } })
    await waitFor(() => expect(api.workspace.switch).toHaveBeenCalledWith(2))
    await waitFor(() => expect(onSwitched).toHaveBeenCalledWith(2))
  })

  it('does not call the endpoint when reselecting the active workspace', async () => {
    api.workspace.list.mockResolvedValueOnce(twoWorkspaces)
    render(<WorkspaceSwitcher />)
    const select = await screen.findByRole('combobox')
    fireEvent.change(select, { target: { value: '1' } })
    expect(api.workspace.switch).not.toHaveBeenCalled()
  })
})
