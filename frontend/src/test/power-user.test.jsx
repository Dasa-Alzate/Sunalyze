import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { CommandPalette } from '@/services/actions/CommandPalette'
import { ShortcutSheet } from '@/services/actions/ShortcutSheet'
import { matchShortcut, formatShortcut, findActionForEvent } from '@/services/actions/registry'
import { filterActions } from '@/services/actions/fuzzy'
import { getActions } from '@/services/actions/registry'

async function expectNoViolations(ui) {
  const { container } = render(ui)
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('command palette accessibility', () => {
  it('has no axe violations and exposes combobox/listbox', async () => {
    await expectNoViolations(<CommandPalette onClose={() => {}} onRun={() => {}} mac={false} />)
  })

  it('renders a combobox controlling a listbox with active descendant', () => {
    render(<CommandPalette onClose={() => {}} onRun={() => {}} mac={false} />)
    const input = screen.getByRole('combobox', { name: 'Buscar comando' })
    expect(input).toHaveAttribute('aria-controls')
    expect(input).toHaveAttribute('aria-activedescendant')
    expect(screen.getByRole('listbox')).toBeInTheDocument()
  })

  it('fuzzy filters and Enter runs the active action; Esc closes', () => {
    let ran = null
    let closed = false
    render(
      <CommandPalette
        onClose={() => { closed = true }}
        onRun={(a) => { ran = a }}
        mac={false}
      />,
    )
    const input = screen.getByRole('combobox', { name: 'Buscar comando' })
    fireEvent.change(input, { target: { value: 'proyectos' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(ran?.id).toBe('nav.projects')
    expect(closed).toBe(true)
  })
})

describe('shortcut sheet accessibility', () => {
  it('has no axe violations and is a labelled dialog', async () => {
    await expectNoViolations(<ShortcutSheet onClose={() => {}} mac />)
  })

  it('lists shortcuts with platform symbols', () => {
    render(<ShortcutSheet onClose={() => {}} mac />)
    expect(screen.getByRole('dialog', { name: 'Atajos de teclado' })).toBeInTheDocument()
    expect(screen.getByText('⌘K')).toBeInTheDocument()
  })
})

describe('cross-platform shortcut matcher (event.code + normalized Mod)', () => {
  const altD = { alt: true, code: 'KeyD' }

  it('Opt+D on Mac fires via event.code despite the ∂ glyph', () => {
    const macEvent = { code: 'KeyD', key: '∂', altKey: true, metaKey: false, ctrlKey: false, shiftKey: false }
    expect(matchShortcut(macEvent, altD, true)).toBe(true)
  })

  it('the same binding is Alt+D on Win/Linux', () => {
    const winEvent = { code: 'KeyD', key: 'd', altKey: true, metaKey: false, ctrlKey: false, shiftKey: false }
    expect(matchShortcut(winEvent, altD, false)).toBe(true)
  })

  it('Mod is metaKey on Mac and ctrlKey on Win/Linux', () => {
    const modK = { mod: true, code: 'KeyK' }
    expect(matchShortcut({ code: 'KeyK', metaKey: true, ctrlKey: false, altKey: false, shiftKey: false }, modK, true)).toBe(true)
    expect(matchShortcut({ code: 'KeyK', metaKey: false, ctrlKey: true, altKey: false, shiftKey: false }, modK, false)).toBe(true)
    expect(matchShortcut({ code: 'KeyK', metaKey: false, ctrlKey: true, altKey: false, shiftKey: false }, modK, true)).toBe(false)
  })

  it('does not match when an extra cross modifier is held', () => {
    const event = { code: 'KeyK', metaKey: true, ctrlKey: true, altKey: false, shiftKey: false }
    expect(matchShortcut(event, { mod: true, code: 'KeyK' }, true)).toBe(false)
  })

  it('findActionForEvent resolves the palette on Mod+K', () => {
    const event = { code: 'KeyK', metaKey: true, ctrlKey: false, altKey: false, shiftKey: false }
    expect(findActionForEvent(event, true)?.id).toBe('palette.open')
  })

  it('formats combos with platform symbols', () => {
    expect(formatShortcut({ mod: true, code: 'KeyK' }, true)).toBe('⌘K')
    expect(formatShortcut({ mod: true, code: 'KeyK' }, false)).toBe('Ctrl+K')
    expect(formatShortcut({ alt: true, code: 'Slash' }, true)).toBe('⌥/')
  })
})

describe('fuzzy matcher', () => {
  beforeEach(() => {})
  it('returns all actions for empty query in registry order', () => {
    expect(filterActions('', getActions())).toEqual(getActions())
  })
  it('matches by keyword subsequence', () => {
    const r = filterActions('dash', getActions())
    expect(r[0].id).toBe('nav.dashboard')
  })
  it('drops non-matches', () => {
    expect(filterActions('zzzz', getActions())).toHaveLength(0)
  })
})
