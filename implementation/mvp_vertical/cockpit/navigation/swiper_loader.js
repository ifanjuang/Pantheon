const SWIPER_VERSION = "14.0.7";

// Subresource Integrity for swiper-bundle.min.js at the pinned version.
// Computed from the npm tarball whose integrity matched the registry's own
// dist.integrity, so it covers exactly the bytes every CDN mirrors. A CDN that
// serves anything else is refused by the browser and the next candidate is
// tried; if none matches, ensureSwiper() reports false and the Cockpit shows a
// visible navigation failure rather than executing unverified third-party code.
const SWIPER_SCRIPT_SRI =
  "sha384-kHWvh6zWFwbm/ld2WlIlTnUiI28TQ4LLnOQqS2L+CaRr4y3AAfMqASByB2yrNY+g";

function loadExternalScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    // Both are required: SRI is only enforced on a cross-origin request that
    // opts into CORS.
    script.crossOrigin = "anonymous";
    script.integrity = SWIPER_SCRIPT_SRI;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error(`Impossible de charger ${src}`));
    document.head.append(script);
  });
}

function markReady(ready) {
  document.documentElement.dataset.swiperReady = ready ? "true" : "false";
  if (ready) document.documentElement.dataset.swiperVersion = SWIPER_VERSION;
  else delete document.documentElement.dataset.swiperVersion;
}

export async function ensureSwiper() {
  if (typeof window.Swiper === "function") {
    markReady(true);
    return true;
  }

  const candidates = [
    `https://cdn.jsdelivr.net/npm/swiper@${SWIPER_VERSION}/swiper-bundle.min.js`,
    `https://unpkg.com/swiper@${SWIPER_VERSION}/swiper-bundle.min.js`,
  ];

  for (const src of candidates) {
    try {
      await loadExternalScript(src);
      if (typeof window.Swiper === "function") {
        markReady(true);
        return true;
      }
    } catch (error) {
      console.warn(`Swiper indisponible depuis ${src}`, error);
    }
  }

  markReady(false);
  return false;
}

export const swiperVersion = SWIPER_VERSION;
