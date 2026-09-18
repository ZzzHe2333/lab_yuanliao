const API = '/api/v1'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || body.message || message
    } catch {}
    throw new Error(message)
  }
  const type = response.headers.get('content-type') || ''
  return type.includes('application/json') ? response.json() : response
}

export const api = {
  stats: () => request('/dashboard/stats'),
  warehouses: () => request('/warehouses'),
  createWarehouse: (body) => request('/warehouses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  updateWarehouse: (id, body) => request(`/warehouses/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  deleteWarehouse: (id) => request(`/warehouses/${id}`, { method: 'DELETE' }),
  chemicals: (params = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => { if (v !== '' && v !== null && v !== undefined) query.set(k, v) })
    return request(`/chemicals${query.size ? `?${query}` : ''}`)
  },
  chemical: (id) => request(`/chemicals/${id}`),
  createChemical: (body) => request('/chemicals', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  updateChemical: (id, body) => request(`/chemicals/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  deleteChemical: (id) => request(`/chemicals/${id}`, { method: 'DELETE' }),
  uploadSds: (id, file) => {
    const form = new FormData(); form.append('file', file)
    return request(`/files/sds/${id}`, { method: 'POST', body: form })
  },
  deleteSds: (id) => request(`/files/sds/${id}`, { method: 'DELETE' }),
  sdsUrl: (id) => `${API}/files/sds/${id}`,
  qrUrl: (id) => `${API}/files/qrcode/${id}`
}
