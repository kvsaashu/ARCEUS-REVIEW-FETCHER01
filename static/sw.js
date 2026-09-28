// Arceus Review Fetcher PRO - Service Worker
const CACHE_NAME = 'arceus-cache-v10';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/js/three.min.js',
  '/static/js/3d_scene.js',
  '/static/js/app.js',
  '/static/manifest.json',
  '/static/icons/logo.png',
  '/static/icons/favicon.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Install: Cache Shell Assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Arceus SW] Caching app shell');
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Arceus SW] Removing old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Network-first for dynamic API, cache-first fallback for static assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // For API and POST requests, always fetch directly from network
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Update cache with fresh version if OK
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback to cache if network is unavailable
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
  );
});

