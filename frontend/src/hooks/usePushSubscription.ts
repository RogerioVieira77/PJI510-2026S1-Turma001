import { useState } from 'react'
import apiClient from '@/api/client'
import { useAuthStore } from '@/store/auth'

const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY as string

/** Converte VAPID public key de Base64url para Uint8Array */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)))
}

interface UsePushSubscriptionReturn {
  isSubscribed: boolean
  isLoading: boolean
  error: string | null
  subscribe: () => Promise<void>
  unsubscribe: () => Promise<void>
}

export function usePushSubscription(): UsePushSubscriptionReturn {
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const user = useAuthStore((s) => s.user)

  async function subscribe() {
    setError(null)
    setIsLoading(true)

    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        throw new Error('Notificações push não são suportadas neste navegador')
      }

      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setError('Permissão de notificação negada pelo usuário')
        return
      }

      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      })

      const json = subscription.toJSON() as {
        endpoint: string
        keys: { p256dh: string; auth: string }
      }

      await apiClient.post('/alertas/subscribe/push', {
        endpoint: json.endpoint,
        p256dh: json.keys.p256dh,
        auth: json.keys.auth,
        usuario_id: user?.id ?? null,
      })

      setIsSubscribed(true)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao ativar notificações'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  async function unsubscribe() {
    setError(null)
    setIsLoading(true)

    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      if (subscription) {
        await subscription.unsubscribe()
      }
      await apiClient.delete('/alertas/subscribe/push')
      setIsSubscribed(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao desativar notificações'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return { isSubscribed, isLoading, error, subscribe, unsubscribe }
}
