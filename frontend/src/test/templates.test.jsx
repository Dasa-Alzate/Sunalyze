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
    setCategory: vi.fn(() => Promise.resolve({})),
    setLabels: vi.fn(() => Promise.resolve({})),
    createCategory: vi.fn((name) => Promise.resolve({ id: 11, name })),
    createLabel: vi.fn((name) => Promise.resolve({ id: 21, name })),
    generate: vi.fn(() => Promise.resolve({ id: 100 })),
    projectDocuments: vi.fn(() => Promise.resolve([
      { id: 100, template_name: 'Mi memoria', template_version: 3, pdf_size_bytes: 2048, generated_at: '2026-06-22T10:00:00Z' },
    ])),
    downloadDocument: vi.fn(() => Promise.resolve(new Blob(['pdf'], { type: 'application/pdf' }))),
  },
  projects: { list: vi.fn(() => Promise.resolve([{ id: 5, cliente: 'ACME' }])) },
}

vi.mock('@/api/client', () => ({ api, csrfToken: () => 'tok' }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))

let TemplatesGallery, TemplateBuilder, VariablePicker, AssignTemplateDialog, ProjectDocuments
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: TemplatesGallery } = await import('@/features/templates/TemplatesGallery'))
  ;({ default: TemplateBuilder } = await import('@/features/templates/TemplateBuilder'))
  ;({ default: VariablePicker } = await import('@/features/templates/VariablePicker'))
  ;({ default: AssignTemplateDialog } = await import('@/features/templates/AssignTemplateDialog'))
  ;({ default: ProjectDocuments } = await import('@/features/templates/ProjectDocuments'))
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

describe('AssignTemplateDialog', () => {
  const installation = {
    id: 50,
    template: { name: 'Mi memoria' },
    category: { id: 10, name: 'Residencial' },
    labels: [{ id: 20, name: 'Urgente' }],
  }

  it('renders category radios and label checkboxes with no axe violations', async () => {
    const { container } = render(
      <AssignTemplateDialog
        installation={installation}
        categories={[{ id: 10, name: 'Residencial' }]}
        labels={[{ id: 20, name: 'Urgente' }]}
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByText('Organizar plantilla')).toBeInTheDocument()
    expect(screen.getByLabelText('Residencial')).toBeChecked()
    await expectNoViolations(container)
  })

  it('saves category and labels and creates a new label', async () => {
    let saved = false
    render(
      <AssignTemplateDialog
        installation={installation}
        categories={[{ id: 10, name: 'Residencial' }]}
        labels={[{ id: 20, name: 'Urgente' }]}
        onClose={() => {}}
        onSaved={() => { saved = true }}
      />,
    )
    fireEvent.change(screen.getByLabelText('Nueva etiqueta'), { target: { value: 'Industrial' } })
    fireEvent.click(screen.getAllByRole('button', { name: 'Crear' })[1])
    await waitFor(() => expect(api.templates.createLabel).toHaveBeenCalledWith('Industrial'))
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(saved).toBe(true))
    expect(api.templates.setCategory).toHaveBeenCalledWith(50, 10)
    expect(api.templates.setLabels).toHaveBeenCalled()
  })
})

describe('ProjectDocuments', () => {
  it('lists documents with metadata and has no axe violations', async () => {
    const { container } = render(<ProjectDocuments templateId={7} canManage />)
    await waitFor(() => expect(screen.getByText('v3')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Generar PDF' })).toBeInTheDocument()
    await expectNoViolations(container)
  })

  it('hides the generate button without manage permission', async () => {
    render(<ProjectDocuments templateId={7} canManage={false} />)
    await waitFor(() => expect(screen.getByText('v3')).toBeInTheDocument())
    expect(screen.queryByRole('button', { name: 'Generar PDF' })).toBeNull()
  })

  it('generates a document via the backend', async () => {
    render(<ProjectDocuments templateId={7} canManage />)
    await waitFor(() => expect(screen.getByText('v3')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Generar PDF' }))
    await waitFor(() => expect(api.templates.generate).toHaveBeenCalledWith(7, 5))
  })
})
