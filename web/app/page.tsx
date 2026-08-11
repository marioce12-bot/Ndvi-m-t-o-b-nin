"use client";

import { useEffect, useMemo, useState } from "react";

type Product = "anomaly" | "ndvi";
type Filter = "all" | Product;

const pentades = [
  { id: "2026-P44", label: "6–10 août 2026", detail: "P44 · 2026" },
  { id: "2026-P43", label: "1–5 août 2026", detail: "P43 · 2026" },
  { id: "2026-P42", label: "26–31 juillet 2026", detail: "P42 · 2026" },
  { id: "2026-P41", label: "21–25 juillet 2026", detail: "P41 · 2026" },
];

const maps = [
  { id: 1, product: "anomaly" as Product, label: "6–10 août 2026", date: "Il y a 18 min", tone: "olive", value: "108 %" },
  { id: 2, product: "ndvi" as Product, label: "1–5 août 2026", date: "Il y a 2 h", tone: "forest", value: "0,62" },
  { id: 3, product: "anomaly" as Product, label: "26–31 juillet 2026", date: "Hier", tone: "sand", value: "96 %" },
  { id: 4, product: "ndvi" as Product, label: "21–25 juillet 2026", date: "Il y a 2 jours", tone: "fern", value: "0,58" },
];

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    calendar: <><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></>,
    download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 20h16"/></>,
    copy: <><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></>,
    arrow: <path d="M5 12h14m-6-6 6 6-6 6"/>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    refresh: <><path d="M20 11a8 8 0 0 0-14.9-3L3 11m0 0V5m0 6h6M4 13a8 8 0 0 0 14.9 3L21 13m0 0v6m0-6h-6"/></>,
    layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>,
    map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15m6-12v15"/></>,
  };
  return <svg aria-hidden="true" className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function MapArtwork({ tone, large = false }: { tone: string; large?: boolean }) {
  return <div className={`map-art map-${tone} ${large ? "map-art-large" : ""}`}>
    <div className="map-grid" />
    <svg className="benin-shape" viewBox="0 0 260 390" aria-label="Aperçu de la carte du Bénin" role="img">
      <path d="M91 15 133 6l25 23 19 4 7 28 18 24-14 24 9 26-13 28 12 31-18 24 6 30-20 24 4 30-28 20-14 30-28 11-18-20-23 2-15-30 7-31-10-29 14-26-4-33 16-25-7-32 19-25-7-30 17-25Z" />
      <path className="map-line" d="M94 75 157 77m-74 50 88 4m-97 48 100 3m-111 48 106 5m-102 43 91 1m-69 42 61-1" />
      <path className="map-line map-line-soft" d="m132 8-6 365M91 15l15 350M157 29l-28 330" />
    </svg>
    <span className="map-label map-label-north">ALIBORI</span>
    <span className="map-label map-label-center">BORGOU</span>
    <span className="map-label map-label-south">ZOU</span>
    <span className="map-scale">0°E&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 4°E</span>
  </div>;
}

export default function HomePage() {
  const [product, setProduct] = useState<Product>("anomaly");
  const [pentade, setPentade] = useState(pentades[0].id);
  const [filter, setFilter] = useState<Filter>("all");
  const [activeMap, setActiveMap] = useState<(typeof maps)[number] | null>(null);
  const [status, setStatus] = useState<"idle" | "processing" | "done">("idle");
  const [toast, setToast] = useState("");

  useEffect(() => { document.title = status === "processing" ? "⏳ Génération… · Cartes NDVI Bénin" : "Cartes NDVI Bénin"; }, [status]);
  useEffect(() => { if (!toast) return; const timer = window.setTimeout(() => setToast(""), 2200); return () => window.clearTimeout(timer); }, [toast]);

  const visibleMaps = useMemo(() => filter === "all" ? maps : maps.filter((item) => item.product === filter), [filter]);
  const selected = pentades.find((item) => item.id === pentade) ?? pentades[0];

  function generate() {
    setStatus("processing");
    window.setTimeout(() => setStatus("done"), 1800);
  }

  function copyLink() { navigator.clipboard?.writeText("https://res.cloudinary.com/ndvi-benin/anomaly_2026-P44.jpg"); setToast("Lien copié"); }

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand">
        <div className="brand-symbol"><span>ND</span><i /></div>
        <div><div className="brand-name">Météo Bénin</div><div className="brand-sub">Observatoire de la végétation</div></div>
      </div>
      <div className="topbar-meta"><span className="live-dot" /> Données eVIIRS <span className="meta-divider" /> Mise à jour pentadale</div>
    </header>

    <section className="hero-row">
      <div><div className="eyebrow">PRODUCTION CARTOGRAPHIQUE <span>·</span> BÉNIN</div><h1>Cartes de végétation</h1><p>Générez et consultez les indicateurs NDVI à 375 m, période par période.</p></div>
      <div className="hero-stats"><div><strong>375</strong><span>m résolution</span></div><div><strong>72</strong><span>pentades / an</span></div><div><strong>12</strong><span>départements</span></div></div>
    </section>

    <section className="workspace-grid">
      <div className="generation-card card">
        <div className="card-heading"><div><span className="section-kicker">NOUVELLE CARTE</span><h2>Paramètres de génération</h2></div><span className="secure-pill"><span className="live-dot" /> Source active</span></div>
        <div className="field-block"><label>Produit cartographique</label><div className="product-toggle"><button className={product === "anomaly" ? "active anomaly-active" : ""} onClick={() => setProduct("anomaly")}><span className="toggle-swatch anomaly-swatch" /><span><strong>NDVI anomalie</strong><small>Pourcentage de la moyenne</small></span></button><button className={product === "ndvi" ? "active" : ""} onClick={() => setProduct("ndvi")}><span className="toggle-swatch ndvi-swatch" /><span><strong>NDVI brut</strong><small>Indice de végétation</small></span></button></div></div>
        <div className="field-block"><label htmlFor="pentade">Période d’analyse</label><div className="select-wrap"><Icon name="calendar" size={17} /><select id="pentade" value={pentade} onChange={(event) => setPentade(event.target.value)}>{pentades.map((item) => <option key={item.id} value={item.id}>{item.label}  ·  {item.detail}</option>)}</select><span className="select-chevron">⌄</span></div><span className="field-hint">Les données les plus récentes sont proposées en premier.</span></div>
        <button className="generate-button" onClick={generate} disabled={status === "processing"}><span>{status === "processing" ? "Génération en cours…" : "Générer la carte"}</span><Icon name="arrow" size={18} /></button>
        <div className={`job-status ${status}`} aria-live="polite">{status === "idle" && <><span className="status-icon"><Icon name="layers" size={17} /></span><span><strong>Prêt à générer</strong><small>Le traitement prend généralement moins de 2 minutes.</small></span></>}{status === "processing" && <><span className="spinner" /><span><strong>Génération en cours</strong><small>Téléchargement, découpage et rendu de la carte…</small></span><b>00:08</b></>}{status === "done" && <><span className="status-icon done-icon">✓</span><span><strong>Carte prête</strong><small>{product === "anomaly" ? "NDVI anomalie" : "NDVI brut"} · {selected.label}</small></span><button onClick={() => setActiveMap({ ...maps[0], product, label: selected.label })}>Voir</button></>}</div>
      </div>
      <div className="preview-card card"><div className="preview-top"><div><span className="section-kicker">APERÇU DU PRODUIT</span><h2>{product === "anomaly" ? "NDVI anomalie" : "NDVI brut"}</h2></div><span className={`product-badge ${product}`}>{product === "anomaly" ? "ANOMALIE" : "NDVI"}</span></div><MapArtwork tone={product === "anomaly" ? "olive" : "forest"} large /><div className="preview-caption"><span><Icon name="map" size={15} /> Bénin · {selected.label}</span><span className="caption-muted">USGS FEWS NET</span></div></div>
    </section>

    <section className="gallery-section"><div className="gallery-heading"><div><div className="eyebrow">ARCHIVE EN TEMPS RÉEL</div><h2>Cartes générées <span>{maps.length}</span></h2></div><div className="filter-tabs"><button className={filter === "all" ? "selected" : ""} onClick={() => setFilter("all")}>Toutes <em>{maps.length}</em></button><button className={filter === "ndvi" ? "selected" : ""} onClick={() => setFilter("ndvi")}>NDVI</button><button className={filter === "anomaly" ? "selected" : ""} onClick={() => setFilter("anomaly")}>Anomalie</button></div></div><div className="gallery-grid">{visibleMaps.map((item) => <button className="gallery-item" key={item.id} onClick={() => setActiveMap(item)}><MapArtwork tone={item.tone} /><div className="gallery-info"><div><span className={`mini-badge ${item.product}`}>{item.product === "anomaly" ? "Anomalie" : "NDVI"}</span><strong>{item.label}</strong></div><span className="gallery-date">{item.date}</span></div><div className="gallery-value">{item.value}</div></button>)}</div></section>

    <footer className="footer"><span>Source : USGS FEWS NET · eVIIRS 375 m</span><span>Plateforme opérationnelle <span className="live-dot" /></span></footer>
    {activeMap && <div className="lightbox" role="dialog" aria-modal="true" aria-label="Visualiseur de carte" onClick={() => setActiveMap(null)}><div className="lightbox-panel" onClick={(event) => event.stopPropagation()}><div className="lightbox-head"><div><span className={`mini-badge ${activeMap.product}`}>{activeMap.product === "anomaly" ? "Anomalie" : "NDVI"}</span><h2>{activeMap.label}</h2></div><button className="icon-button" onClick={() => setActiveMap(null)} aria-label="Fermer"><Icon name="close" /></button></div><MapArtwork tone={activeMap.tone} large /><div className="lightbox-actions"><button className="secondary-button" onClick={copyLink}><Icon name="copy" size={16} /> Copier le lien</button><button className="primary-small"><Icon name="download" size={16} /> Télécharger JPEG</button></div></div></div>}
    {toast && <div className="toast">✓ {toast}</div>}
  </main>;
}
