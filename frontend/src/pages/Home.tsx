import { useEffect, useState } from 'react'
import { getMe, logout, type MeResponse } from '../lib/api'
import { useAuth } from '../stores/auth'

export default function Home() {
  const token = useAuth((s) => s.accessToken)!
  const setToken = useAuth((s) => s.setToken)
  const [me, setMe] = useState<MeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getMe(token)
      .then(setMe)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Error')
        setToken(null) // token inválido → de vuelta al login
      })
  }, [token, setToken])

  async function onLogout() {
    await logout()
    setToken(null)
  }

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow p-8 space-y-4">
          <h1 className="text-2xl font-bold text-slate-800">
            ¡Hola{me ? `, ${me.username}` : ''}! 👋
          </h1>
          <p className="text-slate-600">
            Estás autenticado. Este es el "hello world" protegido del Hito 1: el login generó
            un JWT y esta página lo usó para consultar <code className="text-slate-800">/auth/me</code>.
          </p>

          {error && <p className="text-red-600">{error}</p>}

          {me && (
            <dl className="grid grid-cols-2 gap-2 text-sm bg-slate-50 rounded-lg p-4">
              <dt className="text-slate-500">Usuario</dt>
              <dd className="text-slate-800 font-medium">{me.username}</dd>
              <dt className="text-slate-500">Rol</dt>
              <dd className="text-slate-800 font-medium">{me.role}</dd>
              <dt className="text-slate-500">Empresa (tenant)</dt>
              <dd className="text-slate-800 font-medium">{me.tenant_name}</dd>
              <dt className="text-slate-500">Multi-dispositivo</dt>
              <dd className="text-slate-800 font-medium">{me.allow_multi_device ? 'Sí' : 'No'}</dd>
            </dl>
          )}

          <button
            onClick={onLogout}
            className="rounded-lg bg-slate-800 text-white px-4 py-2 font-medium hover:bg-slate-700"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  )
}
