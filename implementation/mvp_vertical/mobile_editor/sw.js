const CACHE = "pantheon-knowledge-shell-r4";
const CACHE_PREFIX = "pantheon-knowledge-shell-";
const SHELL = [
  "./",
  "index.html",
  "styles.css",
  "app.js",
  "variant_review.js",
  "manifest.webmanifest",
  "icon.svg",
];
const API_PREFIXES = [
  "/projects/",
  "/documents/",
  "/knowledge/",
  "/edit-requests",
  "/execution-results/",
  "/previews/",
  "/agency/",
  "/work/",
  "/hermes/",
  "/resources/",
  "/health",
];

self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL))));
self.addEventListener("activate", event => event.waitUntil(
  caches.keys().then(keys => Promise.all(
    keys
      .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
      .map(key => caches.delete(key))
  )).then(() => self.clients.claim())
));
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const path = new URL(event.request.url).pathname;
  if (API_PREFIXES.some(prefix => path === prefix || path.startsWith(prefix))) return;
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request)));
});
