import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const catalog = [
  { entity: 'project', label: 'Proyecto', vars: [
    { path: 'project.cliente', label: 'Cliente', tipo: 'text' },
    { path: 'project.kwp', label: 'Potencia pico (kWp)', tipo: 'number' },
  ] },
  { entity: 'panel', label: 'Panel', vars: [
    { path: 'panel.power', label: 'Potencia del panel (W)', tipo: 'number' },
  ] },
]

const template = {
  id: 7, org_id: 3, scope: 'org', kind: 'memoria_calculo', name: 'Mi memoria',
  description: 'Demo', status: 'draft', is_system: false,
  content: [{ id: 's1', type: 'text', title: 'Intro', body: 'Hola {{ project.cliente }}' }],
}

const api = {
  templates: {
    bank: vi.fn(() => Promise.resolve([{ id: 1, kind: 'memoria_calculo', name: 'Banco A', description: 'Oficial', status: 'published', is_system: true }])),
    list: vi.fn(() => Promise.resolve([{ id: 7, kind: 'memoria_calculo', name: 'Mi memoria', description: 'Demo', status: 'draft', is_system: false }])),
    library: vi.fn(() => Promise.resolve([])),
    categories: vi.fn(() => Promise.resolve([{ id: 10, name: 'Residencial' }])),
    labels: vi.fn(() => Promise.resolve([{ id: 20, name: 'Urgente' }])),
    variables: vi.fn(() => Promise.resolve(catalog)),
    get: vi.fn(() => Promise.resolve(template)),
    preview: vi.fn(() => Promise.resolve({ sections: [], html: '<section><h2>Intro</h2></section>' })),
    install: vi.fn(() => Promise.resolve({ id: 99 })),
    saveContent: vi.fn(() => Promise.resolve({ version: 2 })),
    publish: vi.fn(() => Promise.resolve({ status: 'published' })),
    create: vi.fn(() => Promise.resolve({ id: 8 })),
    setFavorite: vi.fn(() => Promise.resolve({})),
  },
  projects: { list: vi.fn(() => Promise.resolve([{ id: 5, cliente: 'ACME' }])) },
}

vi.mock('@/api/client', () => ({ api, csrfToken: () => 'tok' }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))

let TemplatesGallery, TemplateBuilder, VariablePicker
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: TemplatesGallery } = await import('@/features/templates/TemplatesGallery'))
  ;({ default: TemplateBuilder } = await import('@/features/templates/TemplateBuilder'))
  ;({ default: VariablePicker } = await import('@/features/templates/VariablePicker'))
})

async function expectNoViolations(container) {
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('TemplatesGallery', () => {
  it('renders tabs and bank cards with no axe violations', async () => {
    const { container } = render(<MemoryRouter><TemplatesGallery /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Banco A')).toBeInTheDocument())
    expect(screen.getByRole('tablist', { name: 'Vistas de plantillas' })).toBeInTheDocument()
    await expectNoViolations(container)
  })

  it('switches to the library tab and shows category/label filters', async () => {
    render(<MemoryRouter><TemplatesGallery /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Banco A')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('tab', { name: /Biblioteca/ }))
    expect(screen.getByLabelText('Categoría')).toBeInTheDocument()
    expect(screen.getByLabelText('Etiqueta')).toBeInTheDocument()
  })
})

describe('TemplateBuilder', () => {
  function renderBuilder() {
    return render(
      <MemoryRouter initialEntries={['/app/plantillas/7']}>
        <Routes>
          <Route path="/app/plantillas/:id" element={<TemplateBuilder />} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('loads sections and has no axe violations', async () => {
    const { container } = renderBuilder()
    await waitFor(() => expect(screen.getByDisplayValue('Intro')).toBeInTheDocument())
    expect(api.templates.get).toHaveBeenCalledWith(7)
    await expectNoViolations(container)
  })

  it('adds a section and saves content to the backend', async () => {
    renderBuilder()
    await waitFor(() => expect(screen.getByDisplayValue('Intro')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Añadir sección' }))
    expect(screen.getByText('Sección 2')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(api.templates.saveContent).toHaveBeenCalled())
    const [tid, payload] = api.templates.saveContent.mock.calls[0]
    expect(tid).toBe(7)
    expect(payload.content.length).toBe(2)
  })
})

describe('VariablePicker', () => {
  it('renders the catalog and builds a filtered expression with no axe violations', async () => {
    let inserted = null
    const { container } = render(
      <VariablePicker kind="memoria_calculo" onInsert={(e) => { inserted = e }} onClose={() => {}} />,
    )
    await waitFor(() => expect(screen.getByLabelText('Propiedad')).toBeInTheDocument())
    await expectNoViolations(container)

    fireEvent.change(screen.getByLabelText('Propiedad'), { target: { value: 'project.kwp' } })
    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'number' } })
    fireEvent.change(screen.getByLabelText('Decimales'), { target: { value: '1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Insertar' }))
    expect(inserted).toBe('{{ project.kwp | number(1) }}')
  })
})
