import * as pdfjsLib from "./vendor/pdfjs/build/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL("./vendor/pdfjs/build/pdf.worker.mjs", import.meta.url).toString();

class PantheonPdfReader {
  constructor(root) {
    this.root = root;
    this.pages = root.querySelector("[data-pdf-pages]");
    this.scroll = root.querySelector("[data-pdf-scroll]");
    this.pageStrip = root.querySelector("[data-pdf-page-strip]");
    this.comment = root.querySelector("[data-pdf-comment]");
    this.toggle = root.querySelector("[data-pdf-annotate-toggle]");
    this.pdf = null;
    this.scale = 1;
    this.activePage = 1;
    this.tool = "select";
    this.enabled = false;
    this.layers = [];
    this.onMark = () => {};
    this.renderToken = 0;
    root.addEventListener("click", (event) => this.onClick(event));
    this.scroll.addEventListener("scroll", () => this.updateCurrentPage(), { passive: true });
    this.pages.addEventListener("pointerdown", (event) => this.onPointerDown(event));
    this.pages.addEventListener("pointerup", (event) => this.onPointerUp(event));
    this.pages.addEventListener("pointercancel", () => { this.drawing = null; });
    root.querySelector("[data-pdf-send-to-hermes]").addEventListener("click", () => root.dispatchEvent(new CustomEvent("pdfreader:ask")));
  }

  async open(url, onMark) {
    this.close();
    this.onMark = onMark || (() => {});
    this.pages.replaceChildren();
    this.scale = 1;
    try {
      this.pdf = await pdfjsLib.getDocument({ url }).promise;
      this.pageStrip.replaceChildren();
      const token = ++this.renderToken;
      for (let n = 1; n <= this.pdf.numPages; n += 1) {
        const pageButton = document.createElement("button");
        pageButton.type = "button";
        pageButton.dataset.pdfPage = String(n);
        pageButton.textContent = `P${n}`;
        pageButton.setAttribute("aria-label", `Afficher la page ${n}`);
        this.pageStrip.append(pageButton);
        const wrap = document.createElement("section");
        wrap.className = "pdf-reader-page";
        wrap.dataset.page = String(n);
        const canvas = document.createElement("canvas");
        canvas.setAttribute("aria-label", `Page ${n}`);
        const overlay = document.createElement("canvas");
        overlay.className = "pdf-reader-overlay";
        wrap.append(canvas, overlay);
        this.pages.append(wrap);
      }
      await this.renderAll(token);
      this.applyConfig({});
      this.goToPage(1);
    } catch (error) {
      this.pages.innerHTML = `<p class="ocr-preview-empty">Impossible d’ouvrir le PDF : ${this.escape(error.message || "erreur inconnue")}</p>`;
      throw error;
    }
  }

  escape(value) { const el = document.createElement("span"); el.textContent = value; return el.innerHTML; }

  close() {
    this.renderToken += 1;
    if (this.pdf) this.pdf.destroy();
    this.pdf = null;
    this.pages.replaceChildren();
    this.layers = [];
    this.drawing = null;
  }

  async renderAll(token = ++this.renderToken) {
    if (!this.pdf) return;
    for (const pageEl of this.pages.querySelectorAll(".pdf-reader-page")) {
      if (token !== this.renderToken) return;
      const n = Number(pageEl.dataset.page);
      const page = await this.pdf.getPage(n);
      const base = page.getViewport({ scale: 1 });
      const fit = Math.min((this.scroll.clientWidth - 32) / base.width, 1.45);
      const viewport = page.getViewport({ scale: Math.max(.35, fit * this.scale) });
      const canvas = pageEl.querySelector("canvas:not(.pdf-reader-overlay)");
      const overlay = pageEl.querySelector(".pdf-reader-overlay");
      for (const c of [canvas, overlay]) {
        c.width = Math.floor(viewport.width);
        c.height = Math.floor(viewport.height);
      }
      const ctx = canvas.getContext("2d");
      await page.render({ canvasContext: ctx, viewport }).promise;
    }
    this.drawLayers();
  }

  applyConfig(config) {
    if (typeof config.enabled === "boolean") this.enabled = config.enabled;
    if (config.tool) this.tool = config.tool;
    if (Array.isArray(config.layers)) this.layers = config.layers;
    this.root.classList.toggle("is-annotating", this.enabled);
    this.toggle.setAttribute("aria-pressed", String(this.enabled));
    for (const button of this.root.querySelectorAll("[data-pdf-tool]")) button.setAttribute("aria-pressed", String(button.dataset.pdfTool === this.tool));
    this.drawLayers();
  }

  onClick(event) {
    const page = event.target.closest("[data-pdf-page]");
    if (page) this.goToPage(page.dataset.pdfPage === "prev" ? this.currentPage() - 1 : this.currentPage() + 1);
    const zoom = event.target.closest("[data-pdf-zoom]");
    if (zoom && this.pdf) {
      if (zoom.dataset.pdfZoom === "in") this.scale = Math.min(3, this.scale * 1.2);
      if (zoom.dataset.pdfZoom === "out") this.scale = Math.max(.35, this.scale / 1.2);
      if (zoom.dataset.pdfZoom === "fit") this.scale = 1;
      void this.renderAll();
    }
    const tool = event.target.closest("[data-pdf-tool]");
    if (tool) { this.tool = tool.dataset.pdfTool; this.applyConfig({ tool: this.tool }); }
    if (event.target.closest("[data-pdf-annotate-toggle]")) this.applyConfig({ enabled: !this.enabled });
  }

  currentPage() { return this.activePage; }
  goToPage(n, shouldScroll = true) {
    const page = Math.max(1, Math.min(this.pdf?.numPages || 1, Number(n) || 1));
    this.activePage = page;
    for (const button of this.pageStrip.querySelectorAll("[data-pdf-page]")) {
      const active = Number(button.dataset.pdfPage) === page;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    }
    if (shouldScroll) this.pages.querySelector(`[data-page="${page}"]`)?.scrollIntoView({ block: "start", behavior: "smooth" });
  }
  updateCurrentPage() {
    let best = null;
    let distance = Infinity;
    for (const page of this.pages.querySelectorAll("[data-page]")) {
      const d = Math.abs(page.getBoundingClientRect().top - this.scroll.getBoundingClientRect().top);
      if (d < distance) { distance = d; best = page; }
    }
    if (best && Number(best.dataset.page) !== this.activePage) this.goToPage(Number(best.dataset.page), false);
  }

  coordinates(event, pageEl) {
    const rect = pageEl.getBoundingClientRect();
    return { x: Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)), y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)) };
  }
  onPointerDown(event) {
    if (!this.enabled || this.tool === "select") return;
    const pageEl = event.target.closest(".pdf-reader-page");
    if (!pageEl) return;
    event.preventDefault();
    const start = this.coordinates(event, pageEl);
    this.drawing = { page: Number(pageEl.dataset.page), start, end: start, pageEl };
    pageEl.setPointerCapture?.(event.pointerId);
  }
  onPointerUp(event) {
    if (!this.drawing) return;
    const d = this.drawing;
    d.end = this.coordinates(event, d.pageEl);
    const geometry = this.tool === "point" ? { type: "point", x: d.start.x, y: d.start.y }
      : this.tool === "circle" ? { type: "circle", cx: d.start.x, cy: d.start.y, radius: Math.max(Math.abs(d.end.x - d.start.x), Math.abs(d.end.y - d.start.y)) }
        : { type: this.tool, x1: d.start.x, y1: d.start.y, x2: d.end.x, y2: d.end.y };
    this.onMark({ page: d.page, geometry, comment: this.comment.value.trim() });
    this.drawing = null;
  }
  drawLayers() {
    for (const pageEl of this.pages.querySelectorAll(".pdf-reader-page")) {
      const c = pageEl.querySelector(".pdf-reader-overlay");
      if (!c) continue;
      const ctx = c.getContext("2d");
      ctx.clearRect(0, 0, c.width, c.height);
      const sx = c.width; const sy = c.height;
      for (const layer of this.layers.filter((item) => item.visible !== false)) {
        for (const mark of layer.annotations || []) {
          if (Number(mark.page) !== Number(pageEl.dataset.page) || !mark.geometry) continue;
          const g = mark.geometry; ctx.strokeStyle = layer.owner === "hermes" ? "#16865a" : "#1565c0"; ctx.fillStyle = ctx.strokeStyle; ctx.lineWidth = 3;
          const x = (p) => p.x * sx; const y = (p) => p.y * sy;
          ctx.beginPath();
          if (g.type === "point") { ctx.arc(x(g), y(g), 7, 0, Math.PI * 2); ctx.fill(); }
          else if (g.type === "circle") { ctx.arc(x({x:g.cx,y:g.cy}), y({x:g.cx,y:g.cy}), g.radius * Math.min(sx, sy), 0, Math.PI * 2); ctx.stroke(); }
          else if (Number.isFinite(g.x1) && Number.isFinite(g.x2)) { const start={x:g.x1,y:g.y1}, end={x:g.x2,y:g.y2}; ctx.moveTo(x(start), y(start)); ctx.lineTo(x(end), y(end)); ctx.stroke(); if (g.type === "arrow") { const a = Math.atan2(y(end)-y(start), x(end)-x(start)); ctx.beginPath(); ctx.moveTo(x(end),y(end)); ctx.lineTo(x(end)-12*Math.cos(a-.45),y(end)-12*Math.sin(a-.45)); ctx.lineTo(x(end)-12*Math.cos(a+.45),y(end)-12*Math.sin(a+.45)); ctx.closePath(); ctx.fill(); } }
        }
      }
    }
  }
}

const root = document.getElementById("document-reader-pdf");
window.PantheonPdfReader = new PantheonPdfReader(root);
window.PantheonPdfReaderReady = Promise.resolve(window.PantheonPdfReader);
window.dispatchEvent(new Event("pantheon-pdf-reader-ready"));
