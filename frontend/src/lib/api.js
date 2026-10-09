import axios from 'axios'

const configuredApiUrl = import.meta.env.VITE_API_URL || '/api'
const apiBaseUrl = (() => {
  if (configuredApiUrl.startsWith('/')) return configuredApiUrl
  const baseUrl = configuredApiUrl.startsWith('http')
    ? configuredApiUrl
    : `https://${configuredApiUrl}`
  const normalizedUrl = baseUrl.replace(/\/+$/, '')
  return /\/api$/i.test(normalizedUrl) ? normalizedUrl : `${normalizedUrl}/api`
})()

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = window.sessionStorage.getItem('educore.access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
