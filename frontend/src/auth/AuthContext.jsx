import { useCallback, useEffect, useMemo, useState } from 'react'
import AuthContext from './authContext'
import api from '../lib/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(window.sessionStorage.getItem('educore.access')))

  useEffect(() => {
    if (!window.sessionStorage.getItem('educore.access')) return
    api.get('/auth/me/')
      .then(({ data }) => setUser(data))
      .catch(() => {
        window.sessionStorage.removeItem('educore.access')
        window.sessionStorage.removeItem('educore.refresh')
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (credentials) => {
    const { data } = await api.post('/auth/token/', credentials)
    window.sessionStorage.setItem('educore.access', data.access)
    window.sessionStorage.setItem('educore.refresh', data.refresh)
    try {
      const profile = await api.get('/auth/me/')
      setUser(profile.data)
      return profile.data
    } catch (error) {
      window.sessionStorage.removeItem('educore.access')
      window.sessionStorage.removeItem('educore.refresh')
      throw error
    }
  }, [])

  const refreshUser = useCallback(async () => {
    const { data } = await api.get('/auth/me/')
    setUser(data)
    return data
  }, [])

  const logout = useCallback(() => {
    window.sessionStorage.removeItem('educore.access')
    window.sessionStorage.removeItem('educore.refresh')
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshUser }),
    [user, loading, login, logout, refreshUser],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
