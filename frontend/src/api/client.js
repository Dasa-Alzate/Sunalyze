function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

export function csrfToken() {
  return getCookie('csrf_token')
}

const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

async function request(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (MUTATING.has(method)) headers['X-CSRFToken'] = getCookie('csrf_token')
  const res = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  })
  const text = await res.text()
  const data = text ? safeJson(text) : null
  if (!res.ok) {
    const message = (data && (data.error || data.message)) || `Error ${res.status}`
    throw new ApiError(message, res.status, data)
  }
  return data
}

function safeJson(text) {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

const get = (p) => request(p)
const post = (p, body) => request(p, { method: 'POST', body: JSON.stringify(body) })
const put = (p, body) => request(p, { method: 'PUT', body: JSON.stringify(body) })
const patch = (p, body) => request(p, { method: 'PATCH', body: JSON.stringify(body) })
const del = (p, body) => request(p, body !== undefined ? { method: 'DELETE', body: JSON.stringify(body) } : { method: 'DELETE' })

export const api = {
  panels: {
    list: () => get('/api/panels'),
    create: (b) => post('/api/panels', b),
    update: (id, b) => put(`/api/panels/${id}`, b),
    remove: (id) => del(`/api/panels/${id}`),
  },
  inverters: {
    list: () => get('/api/inverters'),
    create: (b) => post('/api/inverters', b),
    update: (id, b) => put(`/api/inverters/${id}`, b),
    remove: (id) => del(`/api/inverters/${id}`),
  },
  wires: {
    list: () => get('/api/wires'),
    create: (b) => post('/api/wires', b),
    update: (id, b) => put(`/api/wires/${id}`, b),
    remove: (id) => del(`/api/wires/${id}`),
  },
  projects: {
    list: (estado) => get(`/api/projects${estado && estado !== 'todos' ? `?estado=${estado}` : ''}`),
    get: (id) => get(`/api/projects/${id}`),
    create: (b) => post('/api/projects', b),
    update: (id, b) => put(`/api/projects/${id}`, b),
    remove: (id) => del(`/api/projects/${id}`),
    duplicate: (id) => post(`/api/projects/${id}/duplicate`),
  },
  catalogs: {
    list: () => get('/api/catalogs'),
    create: (b) => post('/api/catalogs', b),
    remove: (id) => del(`/api/catalogs/${id}`),
    subscribe: (id) => post(`/api/catalogs/${id}/subscribe`, {}),
    unsubscribe: (id) => post(`/api/catalogs/${id}/unsubscribe`, {}),
  },
  marketplace: {
    list: () => get('/api/marketplace'),
  },
  analyze: (b) => post('/api/panel-analysis', b),
  members: {
    list: () => get('/api/members'),
    changeRole: (userId, role) => patch(`/api/members/${userId}`, { role }),
    remove: (userId) => del(`/api/members/${userId}`),
  },
  invitations: {
    create: (b) => post('/api/invitations', b),
    revoke: (id) => del(`/api/invitations/${id}`),
    get: (token) => get(`/api/invitations/${token}`),
    accept: (token) => post(`/api/invitations/${token}/accept`, {}),
  },
  admin: {
    flags: () => get('/api/admin/flags'),
    upsertFlag: (b) => post('/api/admin/flags', b),
    setOverride: (key, b) => post(`/api/admin/flags/${key}/override`, b),
    clearOverride: (key, b) => del(`/api/admin/flags/${key}/override`, b),
    organizations: () => get('/api/admin/organizations'),
    users: () => get('/api/admin/users'),
  },
  auth: {
    me: () => get('/api/auth/me'),
    register: (b) => post('/api/auth/register', b),
    login: (b) => post('/api/auth/login', b),
    logout: () => post('/api/auth/logout', {}),
    forgotPassword: (b) => post('/api/auth/forgot-password', b),
    resetPassword: (b) => post('/api/auth/reset-password', b),
    verifyEmail: (b) => post('/api/auth/verify-email', b),
  },
}
