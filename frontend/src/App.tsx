import Login from './pages/Login'
import Home from './pages/Home'
import { useAuth } from './stores/auth'

export default function App() {
  const token = useAuth((s) => s.accessToken)
  return token ? <Home /> : <Login />
}
