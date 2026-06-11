import { create } from 'zustand'

interface AuthState {
  accessToken: string | null
  setToken: (token: string | null) => void
}

/** Estado de sesión en memoria. El access token vive aquí; el refresh token
 *  va en una cookie HttpOnly gestionada por el backend (no accesible por JS). */
export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  setToken: (token) => set({ accessToken: token }),
}))
