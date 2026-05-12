import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { axe } from 'vitest-axe'
import {
  Btn,
  IconBtn,
  Field,
  SelectField,
  Badge,
  Metric,
  Card,
  Scrim,
  Topbar,
  ExportMenu,
  ErrorState,
} from '@/shared/ui'

async function expectNoViolations(ui) {
  const { container } = render(ui)
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('design-system primitives have no axe violations', () => {
  it('Btn', async () => {
    await expectNoViolations(<Btn icon="plus">Crear proyecto</Btn>)
  })

  it('IconBtn carries an accessible name', async () => {
    await expectNoViolations(<IconBtn icon="settings" label="Ajustes" />)
  })

  it('Field with label, hint and error', async () => {
    await expectNoViolations(
      <Field id="cliente" label="Cliente" hint="Razón social" required />,
    )
  })

  it('Field in error state', async () => {
    await expectNoViolations(
      <Field id="potencia" label="Potencia" error="Valor requerido" required />,
    )
  })

  it('SelectField', async () => {
    await expectNoViolations(
      <SelectField
        id="tipo"
        label="Tipo de instalación"
        options={[
          { value: 'res', label: 'Residencial' },
          { value: 'ind', label: 'Industrial' },
        ]}
      />,
    )
  })

  it('Badge', async () => {
    await expectNoViolations(<Badge tone="success" icon="check">Validado</Badge>)
  })

  it('Metric', async () => {
    await expectNoViolations(<Metric label="Producción" value="12.4" unit="MWh" />)
  })

  it('ExportMenu trigger', async () => {
    await expectNoViolations(<ExportMenu label="Exportar" />)
  })

  it('ErrorState', async () => {
    await expectNoViolations(<ErrorState message="No se pudo cargar." />)
  })
})

describe('composed views have no axe violations', () => {
  it('Topbar landmark with heading', async () => {
    await expectNoViolations(
      <Topbar title="Proyectos" crumb="Inicio" actions={<Btn>Nuevo</Btn>} />,
    )
  })

  it('Card with a form', async () => {
    await expectNoViolations(
      <main>
        <Card className="sun-card--pad">
          <form aria-label="Datos del proyecto">
            <Field id="nombre" label="Nombre" required />
            <SelectField id="region" label="Región" options={['Norte', 'Sur']} />
            <Btn>Guardar</Btn>
          </form>
        </Card>
      </main>,
    )
  })

  it('Scrim dialog with focusable content', async () => {
    await expectNoViolations(
      <Scrim label="Editar proyecto" onClose={() => {}}>
        <div className="sun-drawer">
          <header className="sun-drawer__head"><h3>Editar proyecto</h3></header>
          <div className="sun-drawer__body">
            <Field id="alias" label="Alias" />
          </div>
          <footer className="sun-drawer__foot">
            <Btn variant="secondary">Cancelar</Btn>
            <Btn>Guardar</Btn>
          </footer>
        </div>
      </Scrim>,
    )
  })
})
