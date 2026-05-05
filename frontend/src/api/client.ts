import axios from 'axios'
import { useAuthStore } from '@/store/auth'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Request: attach Bearer token ──────────────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response: handle 401 → refresh token ─────────────────────────────────────
type QueueEntry = { resolve: (token: string) => void; reject: (reason: unknown) => void }
let isRefreshing = false
let failedQueue: QueueEntry[] = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((entry) => {
    if (error) entry.reject(error)
    else entry.resolve(token!)
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const axiosError = error as any
    const originalRequest = axiosError.config

    if (axiosError.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error)
    }

    const { refreshToken, setAuth, clearAuth, user } = useAuthStore.getState()

    if (!refreshToken) {
      clearAuth()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return apiClient(originalRequest)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const res = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
      const { access_token, refresh_token: newRefresh } = res.data as {
        access_token: string
        refresh_token: string
      }
      setAuth(access_token, newRefresh, user!)
      processQueue(null, access_token)
      originalRequest.headers.Authorization = `Bearer ${access_token}`
      return apiClient(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearAuth()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default apiClient
