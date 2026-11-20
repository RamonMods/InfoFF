/* --- InfoFF: cache do site para abrir rápido e funcionar offline na casca. --- */

const CACHE = "infoff-v3";

const CASCA = [
  "./",
  "./index.html",
  "./site.css?v=2",
  "./app.js?v=2",
  "./manifest.json",
  "./assets/favicon.svg",
  "./assets/icon-192.png",
  "./assets/fonts/fonts.css",
  "./assets/fonts/instrument-serif-normal-400.woff2",
  "./assets/fonts/instrument-serif-italic-400.woff2",
  "./assets/fonts/inter-tight-normal-400.woff2",
  "./assets/fonts/inter-tight-normal-500.woff2",
  "./assets/fonts/inter-tight-normal-600.woff2",
  "./assets/fonts/jetbrains-mono-normal-400.woff2",
  "./assets/fonts/jetbrains-mono-normal-700.woff2",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((chaves) => Promise.all(chaves.filter((chave) => chave !== CACHE).map((chave) => caches.delete(chave))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const pedido = evento.request;
  if (pedido.method !== "GET") return;

  const url = new URL(pedido.url);
  if (url.origin !== location.origin) return;

  /* --- navegação: rede primeiro, cache como rede de segurança. --- */
  if (pedido.mode === "navigate") {
    evento.respondWith(
      fetch(pedido)
        .then((resposta) => {
          const copia = resposta.clone();
          caches.open(CACHE).then((cache) => cache.put("./index.html", copia));
          return resposta;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  /* --- arquivos estáticos: cache primeiro. --- */
  evento.respondWith(
    caches.match(pedido).then((guardado) => guardado || fetch(pedido).then((resposta) => {
      if (resposta.ok) {
        const copia = resposta.clone();
        caches.open(CACHE).then((cache) => cache.put(pedido, copia));
      }
      return resposta;
    }))
  );
});
