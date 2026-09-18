const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = sessionStorage.getItem('whoosh-cms-token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && typeof options.body !== 'string' && !(options.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
    options.body = JSON.stringify(options.body)
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 401) {
    sessionStorage.removeItem('whoosh-cms-token')
    window.dispatchEvent(new Event('cms:logout'))
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.detail || `Request failed (${response.status})`)
  return payload
}

export const api = {
  login: (email, password) => request('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ username: email, password }) }),
  me: () => request('/auth/me'),
  trains: (status) => request(`/trains${status ? `?status_filter=${encodeURIComponent(status)}` : ''}`),
  createTrain: (data) => request('/trains', { method: 'POST', body: data }),
  updateTrain: (id, data) => request(`/trains/${id}`, { method: 'PUT', body: data }),
  updateTrainStatus: (id, status) => request(`/trains/${id}/status`, { method: 'PATCH', body: { status } }),
  carriages: (trainId) => request(`/trains/${trainId}/carriages`),
  createCarriage: (trainId, data) => request(`/trains/${trainId}/carriages`, { method: 'POST', body: data }),
  updateCarriage: (id, data) => request(`/carriages/${id}`, { method: 'PUT', body: data }),
  updateCarriageStatus: (id, status) => request(`/carriages/${id}/status`, { method: 'PATCH', body: { status } }),
  seats: (carriageId) => request(`/carriages/${carriageId}/seats`),
  generateSeats: (carriageId) => request(`/carriages/${carriageId}/seats/generate`, { method: 'POST' }),
}
