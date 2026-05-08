/// <reference lib="webworker" />
import { clientsClaim } from 'workbox-core'
import {
  precacheAndRoute,
  cleanupOutdatedCaches,
  createHandlerBoundToURL,
} from 'workbox-precaching'
import { registerRoute, NavigationRoute } from 'workbox-routing'
import { CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

declare const self: ServiceWorkerGlobalScope

// Assume controle imediato de todas as abas
self.skipWaiting()
clientsClaim()

// Precache do shell da aplicação (index.html, JS, CSS)
// __WB_MANIFEST é injetado pelo vite-plugin-pwa em build time
// eslint-disable-next-line @typescript-eslint/no-explicit-any
precacheAndRoute((self as any).__WB_MANIFEST ?? [])
cleanupOutdatedCaches()

// SPA fallback: qualquer navegação serve index.html do precache
registerRoute(new NavigationRoute(createHandlerBoundToURL('index.html')))

// Runtime cache: /api/v1/publico/status — NetworkFirst, fallback para cache offline
registerRoute(
  ({ url }: { url: URL }) => url.pathname === '/api/v1/publico/status',
  new NetworkFirst({
    cacheName: 'api-publico-cache',
    networkTimeoutSeconds: 5,
    plugins: [new ExpirationPlugin({ maxEntries: 10, maxAgeSeconds: 60 })],
  }),
)

// CacheFirst para assets estáticos SAME-ORIGIN (imagens, fontes, ícones)
// Exclui recursos cross-origin (ex.: tiles do OpenStreetMap) para não cacheear
// respostas opacas que podem estar inválidas ou bloqueadas por CSP.
registerRoute(
  ({ request, url }: { request: Request; url: URL }) =>
    url.origin === self.location.origin &&
    (request.destination === 'image' ||
      request.destination === 'font' ||
      request.destination === 'style'),
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30 * 24 * 60 * 60 })],
  }),
)
