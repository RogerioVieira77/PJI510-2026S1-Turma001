import { useAuthStore } from '@/store/auth'
import { useNavigate } from 'react-router-dom'

// Stub — expandido conforme necessidade do projeto
export default function Admin() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    clearAuth()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Administração</h1>
        <button
          onClick={handleLogout}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
        >
          Sair
        </button>
      </div>
      {user && (
        <p className="mt-2 text-slate-500">
          Logado como <strong>{user.nome}</strong> ({user.role})
        </p>
      )}
    </div>
  )
}
