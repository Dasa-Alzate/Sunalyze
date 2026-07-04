import { useRouteError, isRouteErrorResponse } from 'react-router-dom'

export function RouteError() {
  const error = useRouteError()
  const status = isRouteErrorResponse(error) ? error.status : null
  const detail = isRouteErrorResponse(error)
    ? error.statusText
    : (error && error.message) || 'Error inesperado'

  return (
    <div
      role="alert"
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
        {status ? `Error ${status}` : 'Algo ha ido mal'}
      </h1>
      <p style={{ color: 'var(--text-muted, #666)', maxWidth: 480 }}>{detail}</p>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button type="button" onClick={() => window.location.reload()}>
          Recargar
        </button>
        <a href="/app">Ir al inicio</a>
      </div>
    </div>
  )
}
