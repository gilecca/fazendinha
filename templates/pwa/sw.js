{% load static %}
const CACHE = 'fazendinha-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_URLS = [
  OFFLINE_URL,
  '{% static "css/fazendinha.css" %}',
  '{% static "js/main.js" %}',
  '{% static "icons/icon.svg" %}',
];

// Instala e pré-cacheia o shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// Ativa e remove caches antigos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Só intercepta GET do mesmo origin
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  // Admin, pagamentos e WebSocket → rede direta
  if (
    url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/pagamento/') ||
    url.pathname.startsWith('/ws/')
  ) return;

  // Arquivos estáticos → cache-first (com atualização em background)
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        const networkFetch = fetch(request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE).then(c => c.put(request, clone));
          }
          return response;
        });
        return cached || networkFetch;
      })
    );
    return;
  }

  // Navegação HTML → network-first, fallback para offline
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
  }
});
