function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

export function csrfToken() {
  return getCookie('csrf_token')
}

const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

let unauthorizedHandler = null

export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

function notifyUnauthorized(path, status) {
  if (status === 401 && unauthorizedHandler && !path.startsWith('/api/auth/')) {
    unauthorizedHandler()
  }
}

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
    notifyUnauthorized(path, res.status)
    const message = (data && (data.error || data.message)) || `Error ${res.status}`
    throw new ApiError(message, res.status, data)
  }
  return data
}

async function requestBlob(path, options = {}) {
  const res = await fetch(path, { credentials: 'include', ...options })
  if (!res.ok) {
    notifyUnauthorized(path, res.status)
    const text = await res.text()
    const data = text ? safeJson(text) : null
    const message = (data && (data.error || data.message)) || `Error ${res.status}`
    throw new ApiError(message, res.status, data)
  }
  return res.blob()
}

async function requestForm(path, formData, method = 'POST') {
  const res = await fetch(path, {
    method,
    credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrf_token') },
    body: formData,
  })
  const text = await res.text()
  const data = text ? safeJson(text) : null
  if (!res.ok) {
    notifyUnauthorized(path, res.status)
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
const patch = (p, body) => request(p, { method: 'PATCH', body: JSON.stringify(body) })
const del = (p, body) => request(p, body !== undefined ? { method: 'DELETE', body: JSON.stringify(body) } : { method: 'DELETE' })

export const api = {
  panels: {
    list: () => get('/api/panels'),
    create: (b) => post('/api/panels', b),
    update: (id, b) => patch(`/api/panels/${id}`, b),
    remove: (id) => del(`/api/panels/${id}`),
  },
  inverters: {
    list: () => get('/api/inverters'),
    create: (b) => post('/api/inverters', b),
    update: (id, b) => patch(`/api/inverters/${id}`, b),
    remove: (id) => del(`/api/inverters/${id}`),
  },
  batteries: {
    list: () => get('/api/batteries'),
    create: (b) => post('/api/batteries', b),
    update: (id, b) => patch(`/api/batteries/${id}`, b),
    remove: (id) => del(`/api/batteries/${id}`),
  },
  wires: {
    list: () => get('/api/wires'),
    create: (b) => post('/api/wires', b),
    update: (id, b) => patch(`/api/wires/${id}`, b),
    remove: (id) => del(`/api/wires/${id}`),
  },
  projects: {
    list: (estado) => get(`/api/projects${estado && estado !== 'todos' ? `?estado=${estado}` : ''}`),
    listDeleted: () => get('/api/projects?deleted=true'),
    get: (id) => get(`/api/projects/${id}`),
    create: (b) => post('/api/projects', b),
    update: (id, b) => patch(`/api/projects/${id}`, b),
    remove: (id) => del(`/api/projects/${id}`),
    restore: (id) => post(`/api/projects/${id}/restore`, {}),
    duplicate: (id) => post(`/api/projects/${id}/duplicate`),
  },
  catalogs: {
    list: () => get('/api/catalogs'),
    listDeleted: () => get('/api/catalogs?deleted=true'),
    create: (b) => post('/api/catalogs', b),
    remove: (id) => del(`/api/catalogs/${id}`),
    restore: (id) => post(`/api/catalogs/${id}/restore`, {}),
    subscribe: (id) => post(`/api/catalogs/${id}/subscribe`, {}),
    unsubscribe: (id) => post(`/api/catalogs/${id}/unsubscribe`, {}),
  },
  audit: {
    feed: ({ limit = 50, offset = 0 } = {}) => get(`/api/audit?limit=${limit}&offset=${offset}`),
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
  modules: {
    list: () => get('/api/modules'),
    enable: (key) => post(`/api/modules/${key}/enable`, {}),
    disable: (key) => post(`/api/modules/${key}/disable`, {}),
  },
  admin: {
    flags: () => get('/api/admin/flags'),
    upsertFlag: (b) => post('/api/admin/flags', b),
    setOverride: (key, b) => post(`/api/admin/flags/${key}/override`, b),
    clearOverride: (key, b) => del(`/api/admin/flags/${key}/override`, b),
    organizations: () => get('/api/admin/organizations'),
    users: () => get('/api/admin/users'),
  },
  org: {
    getBranding: () => get('/api/org/branding'),
    setBranding: (b) => patch('/api/org/branding', b),
    logoUrl: () => '/api/org/branding/logo',
    uploadLogo: (file) => {
      const fd = new FormData()
      fd.append('logo', file)
      return requestForm('/api/org/branding/logo', fd)
    },
  },
  workspace: {
    list: () => get('/api/workspace'),
    switch: (orgId) => post('/api/workspace/switch', { org_id: orgId }),
  },
  templates: {
    kinds: () => get('/api/templates/kinds'),
    list: (kind) => get(`/api/templates${kind ? `?kind=${encodeURIComponent(kind)}` : ''}`),
    bank: (kind) => get(`/api/templates/bank${kind ? `?kind=${encodeURIComponent(kind)}` : ''}`),
    variables: (kind) => get(`/api/templates/variables/${encodeURIComponent(kind)}`),
    get: (id) => get(`/api/templates/${id}`),
    create: (b) => post('/api/templates', b),
    update: (id, b) => patch(`/api/templates/${id}`, b),
    remove: (id) => del(`/api/templates/${id}`),
    saveContent: (id, b) => patch(`/api/templates/${id}/content`, b),
    publish: (id) => post(`/api/templates/${id}/publish`, {}),
    preview: (id, projectId) => post(`/api/templates/${id}/preview`, { project_id: projectId }),
    library: ({ favorite, categoryId } = {}) => {
      const qs = []
      if (favorite !== undefined) qs.push(`favorite=${favorite}`)
      if (categoryId !== undefined && categoryId !== null) qs.push(`category_id=${categoryId}`)
      return get(`/api/templates/library${qs.length ? `?${qs.join('&')}` : ''}`)
    },
    install: (id) => post(`/api/templates/${id}/install`, {}),
    uninstall: (instId) => del(`/api/templates/library/${instId}`),
    setFavorite: (instId, isFavorite) => post(`/api/templates/library/${instId}/favorite`, { is_favorite: isFavorite }),
    setCategory: (instId, categoryId) => post(`/api/templates/library/${instId}/category`, { category_id: categoryId }),
    setLabels: (instId, labelIds) => post(`/api/templates/library/${instId}/labels`, { label_ids: labelIds }),
    categories: () => get('/api/templates/categories'),
    createCategory: (name) => post('/api/templates/categories', { name }),
    removeCategory: (id) => del(`/api/templates/categories/${id}`),
    labels: () => get('/api/templates/labels'),
    createLabel: (name) => post('/api/templates/labels', { name }),
    generate: (id, projectId) => post(`/api/templates/${id}/generate`, { project_id: projectId }),
    projectDocuments: (projectId) => get(`/api/projects/${projectId}/documents`),
    downloadDocument: (docId) => requestBlob(`/api/documents/${docId}/download`),
  },
  finance: {
    compute: (projectId, b) => post(`/api/projects/${projectId}/financial/compute`, b),
    scenarios: (projectId) => get(`/api/projects/${projectId}/financial/scenarios`),
    createScenario: (projectId, b) => post(`/api/projects/${projectId}/financial/scenarios`, b),
    getScenario: (projectId, sid) => get(`/api/projects/${projectId}/financial/scenarios/${sid}`),
    updateScenario: (projectId, sid, b) => patch(`/api/projects/${projectId}/financial/scenarios/${sid}`, b),
    removeScenario: (projectId, sid) => del(`/api/projects/${projectId}/financial/scenarios/${sid}`),
  },
  installations: {
    list: () => get('/api/installations'),
    create: (projectId) => post('/api/installations', { project_id: projectId }),
    get: (id) => get(`/api/installations/${id}`),
    update: (id, b) => patch(`/api/installations/${id}`, b),
    performance: (id) => get(`/api/installations/${id}/performance`),
    maintenance: {
      list: (id) => get(`/api/installations/${id}/maintenance`),
      create: (id, b) => post(`/api/installations/${id}/maintenance`, b),
      update: (id, visitId, b) => patch(`/api/installations/${id}/maintenance/${visitId}`, b),
      remove: (id, visitId) => del(`/api/installations/${id}/maintenance/${visitId}`),
    },
    incidents: {
      list: (id) => get(`/api/installations/${id}/incidents`),
      create: (id, b) => post(`/api/installations/${id}/incidents`, b),
      update: (id, incidentId, b) => patch(`/api/installations/${id}/incidents/${incidentId}`, b),
      remove: (id, incidentId) => del(`/api/installations/${id}/incidents/${incidentId}`),
    },
    readings: {
      list: (id) => get(`/api/installations/${id}/readings`),
      create: (id, b) => post(`/api/installations/${id}/readings`, b),
      update: (id, readingId, b) => patch(`/api/installations/${id}/readings/${readingId}`, b),
      remove: (id, readingId) => del(`/api/installations/${id}/readings/${readingId}`),
    },
  },
  notifications: {
    list: (page = 1, perPage = 20) => get(`/api/notifications?page=${page}&per_page=${perPage}`),
    unreadCount: () => get('/api/notifications/unread-count'),
    markRead: (id) => post(`/api/notifications/${id}/read`, {}),
    readAll: () => post('/api/notifications/read-all', {}),
  },
  pendingWork: {
    get: () => get('/api/pending-work'),
  },
  circuit: {
    templates: () => get('/api/circuit/templates'),
    svgUrl: (template, params = {}) => {
      const qs = new URLSearchParams(params).toString()
      return `/api/circuit/${template}${qs ? `?${qs}` : ''}`
    },
  },
  auth: {
    me: () => get('/api/auth/me'),
    updateLocale: (locale) => patch('/api/auth/me', { locale }),
    register: (b) => post('/api/auth/register', b),
    login: (b) => post('/api/auth/login', b),
    logout: () => post('/api/auth/logout', {}),
    forgotPassword: (b) => post('/api/auth/forgot-password', b),
    resetPassword: (b) => post('/api/auth/reset-password', b),
    verifyEmail: (b) => post('/api/auth/verify-email', b),
  },
}
