// Flauna front-end helpers: service worker registration + Web Push subscription
const PHOTO_MAX_SIDE = 2048;
const PHOTO_COMPRESSION_THRESHOLD = 1_500_000;

function resizePhoto(bitmap) {
  const scale = Math.min(1, PHOTO_MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const width = Math.round(bitmap.width * scale);
  const height = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    bitmap.close();
    return Promise.reject(new Error("Nu s-a putut pregăti fotografia."));
  }
  try {
    context.drawImage(bitmap, 0, 0, width, height);
  } finally {
    bitmap.close();
  }

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("Nu s-a putut pregăti fotografia."));
    }, "image/jpeg", 0.85);
  });
}

function formatFileSize(bytes) {
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}

document.querySelectorAll('input[type="file"][accept*="image"]').forEach((input) => {
  const status = document.createElement("p");
  status.className = "photo-status";
  status.setAttribute("aria-live", "polite");
  input.insertAdjacentElement("afterend", status);

  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) {
      status.textContent = "";
      input.setCustomValidity("");
      return;
    }

    input.setCustomValidity("Așteaptă până pregătesc fotografia.");
    status.classList.remove("photo-status--error");
    status.textContent = "Pregătesc fotografia pentru încărcare…";
    try {
      const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
      const needsResize = file.size > PHOTO_COMPRESSION_THRESHOLD
        || Math.max(bitmap.width, bitmap.height) > PHOTO_MAX_SIDE
        || file.type !== "image/jpeg";
      if (!needsResize) {
        bitmap.close();
        status.textContent = "Fotografia este pregătită pentru încărcare.";
        input.setCustomValidity("");
        return;
      }

      const blob = await resizePhoto(bitmap);
      const compressed = new File([blob], `${file.name.replace(/\.[^.]+$/, "")}.jpg`, {
        type: "image/jpeg",
        lastModified: Date.now(),
      });
      const files = new DataTransfer();
      files.items.add(compressed);
      input.files = files.files;
      status.textContent = `Fotografie optimizată: ${formatFileSize(file.size)} → ${formatFileSize(compressed.size)}.`;
      input.setCustomValidity("");
    } catch (error) {
      console.error("Photo preparation failed", error);
      status.classList.add("photo-status--error");
      status.textContent = "Nu am putut citi această fotografie. Încearcă un JPG, PNG sau WebP.";
      input.setCustomValidity("Alege o fotografie JPG, PNG sau WebP care poate fi deschisă.");
    }
  });
});

function urlBase64ToUint8Array(b64) {
  const padding = "=".repeat((4 - (b64.length % 4)) % 4);
  const raw = atob((b64 + padding).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

async function enablePush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    alert("Acest browser nu permite notificări push. Pe iPhone, adaugă mai întâi aplicația pe ecranul principal (Partajează → Adaugă pe ecranul principal) și deschide-o de acolo.");
    return;
  }
  const key = document.body.dataset.vapid;
  if (!key) {
    alert("Cheile VAPID nu sunt setate în fișierul .env (vezi README, pasul 3).");
    return;
  }
  const perm = await Notification.requestPermission();
  if (perm !== "granted") {
    alert("Ai refuzat notificările. Le poți permite din setările browserului pentru acest site.");
    return;
  }
  try {
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(key),
      });
    }
    const r = await fetch("/push/subscribe/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": document.body.dataset.csrf },
      body: JSON.stringify(sub.toJSON()),
    });
    alert(r.ok ? "Notificările sunt active pe acest dispozitiv." : "Eroare la salvarea abonamentului.");
  } catch (e) {
    alert("Nu s-au putut activa notificările: " + e);
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch((e) => console.warn("SW registration failed", e));
}
