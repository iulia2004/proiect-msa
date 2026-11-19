// Flauna service worker: makes the app installable and shows push notifications
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {}); // network only (no offline cache in this MVP)

self.addEventListener("push", (event) => {
  let d = { title: "Flauna", body: "", url: "/" };
  try { d = Object.assign(d, event.data.json()); } catch (_) {}
  event.waitUntil(
    self.registration.showNotification(d.title, {
      body: d.body,
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png",
      data: { url: d.url },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(clients.openWindow(url));
});
