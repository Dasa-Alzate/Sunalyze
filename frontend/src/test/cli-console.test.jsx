import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { CliConsole } from '@/services/actions/CliConsole'
import {
  tokenize,
  splitTokens,
  parse,
  runCommand,
  autocomplete,
  commonPrefix,
} from '@/services/actions/commands'

function makeCtx() {
  return { navigate: vi.fn(), openPalette: vi.fn(), openSheet: vi.fn(), openConsole: vi.fn() }
}

describe('cli tokenizer', () => {
  it('splits on whitespace', () => {
    expect(tokenize('goto projects')).toEqual(['goto', 'projects'])
  })
  it('keeps quoted segments together', () => {
    expect(tokenize('export memoria "id with space"')).toEqual(['export', 'memoria', 'id with space'])
  })
  it('separates flags from positionals', () => {
    const { positional, flags } = splitTokens(['open', '42', '--force', 'yes', '--quiet'])
    expect(positional).toEqual(['open', '42'])
    expect(flags).toEqual({ force: 'yes', quiet: true })
  })
  it('supports --flag=value', () => {
    const { flags } = splitTokens(['--mode=fast'])
    expect(flags).toEqual({ mode: 'fast' })
  })
})

describe('cli parser validation', () => {
  it('parses goto with a valid enum choice', () => {
    const r = parse('goto projects')
    expect(r.error).toBeUndefined()
    expect(r.parsed.args.where).toBe('projects')
  })
  it('rejects an invalid enum choice', () => {
    const r = parse('goto nowhere')
    expect(r.error).toMatch(/no es válido/i)
  })
  it('rejects a missing required arg', () => {
    const r = parse('project open')
    expect(r.error).toMatch(/falta el argumento/i)
  })
  it('errors on unknown command with a fuzzy suggestion', () => {
    const r = parse('gото')
    const r2 = parse('got')
    expect(parse('xyz').error).toMatch(/desconocido/i)
    expect(r2.error).toMatch(/quisiste decir "goto"/i)
    expect(r).toBeTruthy()
  })
  it('errors on unknown subcommand listing options', () => {
    const r = parse('project frobnicate')
    expect(r.error).toMatch(/subcomando desconocido/i)
    expect(r.error).toMatch(/new/)
  })
  it('requires a subcommand for project', () => {
    expect(parse('project').error).toMatch(/subcomando/i)
  })
})

describe('cli execution', () => {
  it('goto runs the matching nav action (navigates)', () => {
    const ctx = makeCtx()
    const res = runCommand('goto projects', ctx)
    expect(res.ok).toBe(true)
    expect(ctx.navigate).toHaveBeenCalledWith('/app/proyectos')
  })
  it('project open navigates with the id', () => {
    const ctx = makeCtx()
    const res = runCommand('project open 42', ctx)
    expect(res.ok).toBe(true)
    expect(ctx.navigate).toHaveBeenCalledWith('/app/diseno/42')
  })
  it('project new runs the new-project action', () => {
    const ctx = makeCtx()
    runCommand('project new', ctx)
    expect(ctx.navigate).toHaveBeenCalledWith('/app/diseno')
  })
  it('export memoria navigates to the memoria id', () => {
    const ctx = makeCtx()
    runCommand('export memoria 7', ctx)
    expect(ctx.navigate).toHaveBeenCalledWith('/app/memoria/7')
  })
  it('help lists commands', () => {
    const res = runCommand('help', makeCtx())
    expect(res.ok).toBe(true)
    expect(res.message).toMatch(/goto/)
    expect(res.message).toMatch(/project new/)
  })
  it('help <cmd> shows usage', () => {
    const res = runCommand('help goto', makeCtx())
    expect(res.message).toMatch(/goto <dashboard/)
  })
  it('unknown command returns ok:false with message', () => {
    const res = runCommand('zzz', makeCtx())
    expect(res.ok).toBe(false)
    expect(res.message).toMatch(/desconocido/i)
  })
})

describe('cli autocomplete', () => {
  it('completes a verb prefix', () => {
    expect(autocomplete('pro')).toEqual(['project'])
  })
  it('completes subverbs', () => {
    expect(autocomplete('project ').sort()).toEqual(['new', 'open'])
  })
  it('completes enum choices for goto', () => {
    expect(autocomplete('goto ')).toContain('projects')
    expect(autocomplete('goto pro')).toEqual(['projects'])
  })
  it('commonPrefix finds the shared head', () => {
    expect(commonPrefix(['project', 'projects'])).toBe('project')
    expect(commonPrefix(['goto', 'help'])).toBe('')
  })
})

describe('cli console component', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('has no axe violations', async () => {
    const { container } = render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('is a labelled modal dialog with a live output log and a command input', () => {
    render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    expect(screen.getByRole('dialog', { name: 'Consola' })).toBeInTheDocument()
    expect(screen.getByRole('log', { name: 'Salida de la consola' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Comando' })).toBeInTheDocument()
  })

  it('Enter runs a command and echoes input plus output', () => {
    const ctx = makeCtx()
    render(<CliConsole onClose={() => {}} ctx={ctx} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.change(input, { target: { value: 'goto projects' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(ctx.navigate).toHaveBeenCalledWith('/app/proyectos')
    expect(screen.getByText('goto projects')).toBeInTheDocument()
    expect(input.value).toBe('')
  })

  it('an invalid command shows an error line', () => {
    render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.change(input, { target: { value: 'goto nowhere' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByText(/no es válido/i)).toBeInTheDocument()
  })

  it('ArrowUp recalls the previous command from history', () => {
    render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.change(input, { target: { value: 'help' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.keyDown(input, { key: 'ArrowUp' })
    expect(input.value).toBe('help')
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    expect(input.value).toBe('')
  })

  it('Tab autocompletes the verb', () => {
    render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.change(input, { target: { value: 'got' } })
    fireEvent.keyDown(input, { key: 'Tab' })
    expect(input.value).toBe('goto ')
  })

  it('Esc closes the console', () => {
    const onClose = vi.fn()
    render(<CliConsole onClose={onClose} ctx={makeCtx()} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('persists history to localStorage', () => {
    const { unmount } = render(<CliConsole onClose={() => {}} ctx={makeCtx()} />)
    const input = screen.getByRole('textbox', { name: 'Comando' })
    fireEvent.change(input, { target: { value: 'help' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    unmount()
    expect(JSON.parse(localStorage.getItem('sunalyze.cli.history'))).toContain('help')
  })
})
