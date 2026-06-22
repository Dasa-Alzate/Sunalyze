import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { I18nProvider, i18n, applyLocale, messageForError, setActiveLocale } from '@/services/i18n'
import { AuthProvider } from '@/services/auth'
import { num, techNum, techDec } from '@/shared/format'
import { LanguageSwitcher } from '@/shared/LanguageSwitcher'

beforeEach(() => {
  i18n.changeLanguage('es')
  setActiveLocale('es')
})

describe('i18n provider', () => {
  it('renders translated content with no axe violations', async () => {
    applyLocale('es')
    const { container } = render(
      <I18nProvider>
        <p>{i18n.t('nav:items.proyectos')}</p>
      </I18nProvider>,
    )
    expect(screen.getByText('Proyectos')).toBeInTheDocument()
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('switching language changes t() output', () => {
    applyLocale('es')
    expect(i18n.t('nav:items.proyectos')).toBe('Proyectos')
    applyLocale('en')
    expect(i18n.t('nav:items.proyectos')).toBe('Projects')
  })
})

describe('language switcher', () => {
  it('changes language locally when not authenticated', async () => {
    applyLocale('es')
    render(
      <I18nProvider>
        <AuthProvider>
          <LanguageSwitcher />
        </AuthProvider>
      </I18nProvider>,
    )
    const select = await screen.findByLabelText(/idioma|language/i)
    expect(select.value).toBe('es')
    fireEvent.change(select, { target: { value: 'en' } })
    await waitFor(() => expect(i18n.language).toBe('en'))
    expect(i18n.t('settings:language.label')).toBe('Language')
  })
})

describe('locale-aware format (UI vs technical)', () => {
  it('UI numbers follow the active locale', () => {
    applyLocale('es')
    expect(num(1234.5)).toContain(',50')
    expect(num(1234.5)).not.toContain('.50')
    applyLocale('en')
    expect(num(1234.5)).toContain('.50')
    expect(num(1234.5)).not.toContain(',50')
  })

  it('technical numbers stay in es-ES regardless of UI locale', () => {
    applyLocale('en')
    expect(techNum(3.5)).toBe('3,50')
    expect(techDec(1234.5)).toContain(',5')
    expect(techDec(1234.5)).not.toContain('.5')
  })
})

describe('error code mapping', () => {
  it('maps a known code to a translated message', () => {
    applyLocale('es')
    const err = { data: { code: 'auth.invalid_credentials' }, message: 'raw backend' }
    expect(messageForError(err)).toBe('Correo o contraseña incorrectos.')
    applyLocale('en')
    expect(messageForError(err)).toBe('Incorrect email or password.')
  })

  it('falls back to backend message when code is unknown', () => {
    const err = { data: { code: 'totally.unknown' }, message: 'mensaje del backend' }
    expect(messageForError(err)).toBe('mensaje del backend')
  })

  it('joins validation details when present', () => {
    const err = { data: { details: [{ msg: 'campo a' }, { msg: 'campo b' }] } }
    expect(messageForError(err)).toBe('campo a · campo b')
  })
})
