import { useEffect, useState } from 'react'

/**
 * Monitora o estado de conectividade do browser.
 * Escuta os eventos `online` e `offline` do `window`.
 */
export function useOffline(): boolean {
  const [offline, setOffline] = useState<boolean>(!navigator.onLine)

  useEffect(() => {
    function handleOnline() { setOffline(false) }
    function handleOffline() { setOffline(true) }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return offline
}
