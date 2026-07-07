import { useEffect, useId, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

export default function WorkspaceSwitcher({ onSwitched }) {
  const { t } = useTranslation('nav')
  const selectId = useId()
  const [workspaces, setWorkspaces] = useState([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    api.workspace.list()
      .then((d) => alive && setWorkspaces(d?.workspaces || []))
      .catch(() => {})
    return () => { alive = false }
  }, [])

  if (workspaces.length < 2) return null

  const active = workspaces.find((w) => w.active)

  async function onChange(e) {
    const orgId = Number(e.target.value)
    if (!orgId || orgId === active?.org_id) return
    setBusy(true)
    try {
      await api.workspace.switch(orgId)
      if (onSwitched) onSwitched(orgId)
      else window.location.reload()
    } catch (err) {
      toast('error', err.message)
      setBusy(false)
    }
  }

  return (
    <div className="sun-langswitch">
      <label className="sr-only" htmlFor={selectId}>{t('workspace')}</label>
      <select
        id={selectId}
        className="sun-select sun-select--sm"
        style={{ width: '100%' }}
        value={active?.org_id ?? ''}
        onChange={onChange}
        disabled={busy}
      >
        {workspaces.map((w) => (
          <option key={w.org_id} value={w.org_id}>{w.nombre}</option>
        ))}
      </select>
    </div>
  )
}
