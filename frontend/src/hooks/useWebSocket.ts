import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/store/auth'

type MessageHandler = (data: unknown) => void

interface UseWebSocketOptions {
  /** Se true, usa a rota /ws/publico/{id} (sem auth). Padrão: false */
  publico?: boolean
}

interface UseWebSocketReturn {
  lastMessage: unknown
  connected: boolean
  reconnecting: boolean
}

const BASE_DELAY_MS = 1_000
const MAX_DELAY_MS = 30_000

export function useWebSocket(
  reservatorioId: number,
  onMessage?: MessageHandler,
  options: UseWebSocketOptions = {},
): UseWebSocketReturn {
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<unknown>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const attemptsRef = useRef(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const unmountedRef = useRef(false)

  const token = useAuthStore.getState().token

  const connect = useCallback(() => {
    if (unmountedRef.current) return

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host

    const url = options.publico
      ? `${proto}://${host}/ws/publico/${reservatorioId}`
      : `${proto}://${host}/ws/dashboard/${reservatorioId}?token=${token ?? ''}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (unmountedRef.current) return
      setConnected(true)
      setReconnecting(false)
      attemptsRef.current = 0
    }

    ws.onmessage = (event: MessageEvent<string>) => {
      if (unmountedRef.current) return
      try {
        const data: unknown = JSON.parse(event.data)
        setLastMessage(data)
        onMessage?.(data)
      } catch {
        // mensagem não-JSON ignorada
      }
    }

    ws.onclose = () => {
      if (unmountedRef.current) return
      setConnected(false)
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [reservatorioId, token, options.publico, onMessage])

  function scheduleReconnect() {
    if (unmountedRef.current) return
    const delay = Math.min(BASE_DELAY_MS * 2 ** attemptsRef.current, MAX_DELAY_MS)
    attemptsRef.current += 1
    setReconnecting(true)
    timeoutRef.current = setTimeout(() => {
      if (!unmountedRef.current) connect()
    }, delay)
  }

  useEffect(() => {
    unmountedRef.current = false
    connect()

    return () => {
      unmountedRef.current = true
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { lastMessage, connected, reconnecting }
}
