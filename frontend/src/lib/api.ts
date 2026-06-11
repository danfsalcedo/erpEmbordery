const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface MeResponse {
  id: number
  username: string
  role: string
  tenant_id: number
  tenant_name: string
  allow_multi_device: boolean
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    return data.detail ?? 'Error inesperado'
  } catch {
    return 'Error inesperado'
  }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getMe(token: string): Promise<MeResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/api/v1/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })
}
