const D3_VERSION = "7.9.0";
const D3_SCRIPT_SRI =
  "sha512-vc58qvvBdrDR4etbxMdlTt4GBQk1qjvyORR2nrsPsFPyrs+/u5c3+1Ct6upOgdZoIl7eq6k3a1UPDSNAQi/32A==";

function hasRequiredD3() {
  return Boolean(
    window.d3
    && typeof window.d3.hierarchy === "function"
    && typeof window.d3.tree === "function"
    && typeof window.d3.select === "function"
  );
}

function loadExternalScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.crossOrigin = "anonymous";
    script.referrerPolicy = "no-referrer";
    script.integrity = D3_SCRIPT_SRI;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error(`Impossible de charger ${src}`));
    document.head.append(script);
  });
}

function markReady(ready) {
  document.documentElement.dataset.d3Ready = ready ? "true" : "false";
  if (ready) document.documentElement.dataset.d3Version = D3_VERSION;
  else delete document.documentElement.dataset.d3Version;
}

export async function ensureD3() {
  if (hasRequiredD3()) {
    markReady(true);
    return true;
  }

  const candidates = [
    `https://cdn.jsdelivr.net/npm/d3@${D3_VERSION}/dist/d3.min.js`,
    `https://cdnjs.cloudflare.com/ajax/libs/d3/${D3_VERSION}/d3.min.js`,
  ];

  for (const src of candidates) {
    try {
      await loadExternalScript(src);
      if (hasRequiredD3()) {
        markReady(true);
        return true;
      }
    } catch (error) {
      console.warn(`D3 indisponible depuis ${src}`, error);
    }
  }

  markReady(false);
  return false;
}

export const d3Version = D3_VERSION;
