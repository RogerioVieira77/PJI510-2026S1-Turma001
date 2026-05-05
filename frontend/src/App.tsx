import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import Admin from '@/pages/Admin'
import Login from '@/pages/Login'
import PublicDashboard from '@/pages/PublicDashboard'
import TechDashboard from '@/pages/TechDashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Público — sem autenticação */}
          <Route path="/" element={<PublicDashboard />} />
          <Route path="/login" element={<Login />} />

          {/* Técnico — requer role gestor ou admin */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={['gestor', 'admin']}>
                <TechDashboard />
              </ProtectedRoute>
            }
          />

          {/* Admin — requer role admin */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Admin />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
