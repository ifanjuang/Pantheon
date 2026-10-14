export function loadClassicScript(src, { parent = document.body } = {}) {
  if (!src) return Promise.reject(new Error("Chemin de script requis"));
  if (!parent) return Promise.reject(new Error("Point de montage de script indisponible"));

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.onload = () => resolve(src);
    script.onerror = () => reject(new Error(`Impossible de charger ${src}`));
    parent.append(script);
  });
}

export async function loadClassicScriptsInOrder(sources, options = {}) {
  for (const src of sources) await loadClassicScript(src, options);
}
