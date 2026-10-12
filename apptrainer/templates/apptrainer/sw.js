{% load static %}/* AppTrainer service worker: acelera los archivos estáticos y muestra una pantalla
   amable sin conexión. NO guarda páginas con datos personales. */
const CACHE = 'apptrainer-v1';
const OFFLINE_URL = "{% url 'apptrainer:offline' %}";
const PRECACHE = [
  OFFLINE_URL,
  "{% static 'apptrainer/app.css' %}",
  "{% static 'apptrainer/app.js' %}",
  "{% static 'apptrainer/icon-192.png' %}",
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
    return;
  }
  if (url.pathname.startsWith("{{ STATIC_URL }}")) {
    event.respondWith(
      caches.open(CACHE).then((cache) =>
        cache.match(req).then((cached) => {
          const red = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => cached);
          return cached || red;
        })
      )
    );
  }
});
