import { useEffect, useMemo, useRef, useState } from 'react'
import { Topbar, Card, Btn, IconBtn, Field, SelectField, Spinner, ErrorState, Icon, Badge } from '@/shared/ui'
import { api, ApiError } from '@/api/client'
import { toast } from '@/services/toast'
import { debounce } from '@/shared/debounce'
import { DEFAULTS, formToComputeBody, hasCapex, formToAssumptions } from './constants'
import AssumptionsForm from './AssumptionsForm'
import ResultsDashboard from './ResultsDashboard'
import ScenarioComparison from './ScenarioComparison'
import SavingsStudy from './SavingsStudy'

const TABS = [
  { key: 'estudio', label: 'Estudio', icon: 'calculator' },
  { key: 'escenarios', label: 'Escenarios', icon: 'git-compare' },
  { key: 'venta', label: 'Estudio de ahorro', icon: 'presentation' },
]

function assumptionsToForm(a) {
  if (!a) return { ...DEFAULTS }
  const form = { ...DEFAULTS }
  const hasBreakdown = a.capex_equipment != null || a.capex_labor != null || a.capex_legalization != null
  form.capexMode = a.capex_total != null && !hasBreakdown ? 'total' : (hasBreakdown ? 'breakdown' : 'total')
  Object.keys(DEFAULTS).forEach((k) => { if (a[k] != null) form[k] = a[k] })
  form.autoRatio = a.self_consumption_ratio == null
  if (a.financing) {
    form.financed = true
    form.financing_amount = a.financing.amount
    form.financing_interest_rate = a.financing.interest_rate
    form.financing_term_years = a.financing.term_years
  }
  return form
}

export default function FinanceWorkspace() {
  const [tab, setTab] = useState('estudio')
  const [projects, setProjects] = useState(null)
  const [projectId, setProjectId] = useState('')
  const [form, setForm] = useState({ ...DEFAULTS })
  const [results, setResults] = useState(null)
  const [computing, setComputing] = useState(false)
  const [computeError, setComputeError] = useState(null)
  const [listError, setListError] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [scenarioName, setScenarioName] = useState('')
  const formRef = useRef(form)
  formRef.current = form

  useEffect(() => {
    let alive = true
    api.projects.list()
      .then((list) => {
        if (!alive) return
        setProjects(list || [])
        setProjectId((list && list[0]?.id) ? String(list[0].id) : '')
      })
      .catch((e) => alive && setListError(e.message))
    return () => { alive = false }
  }, [])

  function loadScenarios(pid) {
    if (!pid) return
    api.finance.scenarios(Number(pid))
      .then((list) => setScenarios(list || []))
      .catch((e) => { setScenarios([]); toast('error', 'No se pudieron cargar los escenarios', e.message) })
  }

  useEffect(() => { loadScenarios(projectId) }, [projectId])

  const runCompute = useMemo(() => debounce((pid, f) => {
    if (!pid || !hasCapex(f)) { setResults(null); return }
    setComputing(true)
    setComputeError(null)
    api.finance.compute(Number(pid), formToComputeBody(f))
      .then((res) => setResults(res))
      .catch((e) => {
        setResults(null)
        setComputeError(e instanceof ApiError ? e.message : 'No se pudo calcular el estudio.')
      })
      .finally(() => setComputing(false))
  }, 400), [])

  useEffect(() => {
    runCompute(projectId, form)
    return () => runCompute.cancel()
  }, [projectId, form, runCompute])

  async function saveScenario() {
    if (!projectId) return
    const f = formRef.current
    if (!hasCapex(f)) { toast('error', 'Indica el CAPEX antes de guardar'); return }
    const body = { name: scenarioName.trim() || `Escenario ${scenarios.length + 1}`, ...formToComputeBody(f), assumptions: formToAssumptions(f) }
    try {
      await api.finance.createScenario(Number(projectId), body)
      toast('success', 'Escenario guardado')
      setScenarioName('')
      loadScenarios(projectId)
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
    }
  }

  async function removeScenario(sid) {
    try {
      await api.finance.removeScenario(Number(projectId), sid)
      loadScenarios(projectId)
    } catch (e) {
      toast('error', 'No se pudo eliminar', e.message)
    }
  }

  function loadFromScenario(s) {
    setForm(assumptionsToForm(s.assumptions))
    setResults(s.results || null)
    setTab('estudio')
  }

  const project = (projects || []).find((p) => String(p.id) === String(projectId)) || null

  if (listError) return <ErrorState message={listError} />
  if (projects === null) return <Spinner label="Cargando proyectos…" />

  return (
    <>
      <Topbar
        title="Estudio financiero"
        crumb="Finanzas"
        actions={
          <SelectField
            label=""
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            options={(projects || []).map((p) => ({ value: String(p.id), label: p.cliente || `Proyecto ${p.id}` }))}
          >
            {projects.length === 0 ? <option value="">Sin proyectos</option> : null}
          </SelectField>
        }
      />

      <div className="sun-tabs" role="tablist" aria-label="Secciones del estudio financiero">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            className={`sun-tab${tab === t.key ? ' sun-tab--active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            <Icon name={t.icon} size={16} />{t.label}
          </button>
        ))}
      </div>

      {tab === 'estudio' && (
        <div className="finance-layout">
          <Card className="sun-card--pad finance-layout__form">
            <AssumptionsForm form={form} onChange={setForm} />
            <div className="finance-save-row">
              <Field
                label="Nombre del escenario"
                placeholder="Contado con subvenciones"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
              />
              <Btn variant="secondary" icon="save" onClick={saveScenario}>Guardar escenario</Btn>
            </div>
          </Card>
          <Card className="sun-card--pad finance-layout__results">
            {computeError ? (
              <ErrorState message={computeError} />
            ) : computing && !results ? (
              <Spinner label="Calculando…" />
            ) : results ? (
              <ResultsDashboard results={results} />
            ) : (
              <p style={{ color: 'var(--text-subtle)', textAlign: 'center', padding: 'var(--space-6)' }}>
                Introduce el CAPEX y el resto de supuestos para ver los resultados.
              </p>
            )}
          </Card>
        </div>
      )}

      {tab === 'escenarios' && (
        <Card className="sun-card--pad">
          {scenarios.length > 0 && (
            <ul className="finance-scenario-list">
              {scenarios.map((s) => (
                <li key={s.id} className="finance-scenario-item">
                  <span>{s.name}{s.is_default && <Badge tone="neutral" icon="star">Por defecto</Badge>}</span>
                  <span className="finance-scenario-item__actions">
                    <Btn variant="secondary" size="sm" icon="pencil" onClick={() => loadFromScenario(s)}>Cargar</Btn>
                    <IconBtn icon="trash-2" label={`Eliminar ${s.name}`} size="sm" onClick={() => removeScenario(s.id)} />
                  </span>
                </li>
              ))}
            </ul>
          )}
          <ScenarioComparison scenarios={scenarios} />
        </Card>
      )}

      {tab === 'venta' && (
        <Card className="sun-card--pad">
          <SavingsStudy project={project} results={results} />
        </Card>
      )}
    </>
  )
}
