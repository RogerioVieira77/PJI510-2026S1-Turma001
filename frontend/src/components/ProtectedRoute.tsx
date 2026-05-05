import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore, type AuthUser } from '@/store/auth'

interface Props {
  children: ReactNode
  allowedRoles: AuthUser['role'][]
}

export default function ProtectedRoute({ children, allowedRoles }: Props) {
  const { token, user } = useAuthStore()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (user && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow">
          <h1 className="text-2xl font-bold text-red-600">403 — Acesso Negado</h1>
          <p className="mt-2 text-slate-600">
            Você não tem permissão para acessar esta página.
          </p>
          <a href="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
            Voltar ao início
          </a>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
