import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter } from 'react-router-dom'
import { TransitionProvider } from '@/services/transition'
import { PrivacyPolicy, Terms, Cookies } from '@/features/legal/Legal'

function renderLegal(ui) {
  return render(
    <MemoryRouter>
      <TransitionProvider>{ui}</TransitionProvider>
    </MemoryRouter>,
  )
}

async function expectNoViolations(container) {
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('legal pages', () => {
  it('Privacy policy renders a single h1 and has no axe violations', async () => {
    const { container } = renderLegal(<PrivacyPolicy />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { level: 1, name: /política de privacidad/i })).toBeInTheDocument()
    await expectNoViolations(container)
  })

  it('Terms renders a single h1 and has no axe violations', async () => {
    const { container } = renderLegal(<Terms />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    await expectNoViolations(container)
  })

  it('Cookies renders a single h1 and has no axe violations', async () => {
    const { container } = renderLegal(<Cookies />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    await expectNoViolations(container)
  })

  it('Privacy policy exposes RGPD rights', () => {
    renderLegal(<PrivacyPolicy />)
    expect(screen.getByText(/derecho al olvido/i)).toBeInTheDocument()
    expect(screen.getAllByText(/portabilidad/i).length).toBeGreaterThan(0)
  })
})
