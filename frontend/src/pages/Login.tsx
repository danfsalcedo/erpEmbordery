import { useState, type FormEvent } from 'react'
import { login } from '../lib/api'
import { useAuth } from '../stores/auth'

export default function Login() {
  const setToken = useAuth((s) => s.setToken)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await login(username, password)
      setToken(access_token)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-white rounded-2xl shadow-lg p-8 space-y-5"
      >
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">ERP Bordados</h1>
          <p className="text-sm text-slate-500 mt-1">Inicia sesión para continuar</p>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700">Usuario</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700">Contraseña</label>
          <input
            type="password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-slate-800 text-white py-2 font-medium hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
