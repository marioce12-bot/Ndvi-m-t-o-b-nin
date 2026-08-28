"use client";

import { useEffect, useMemo, useState } from "react";
import { onAuthStateChanged, sendPasswordResetEmail, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, type User } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";

type Product = "anomaly" | "ndvi";
type Filter = "all" | Product;

const pentades = [
  { id: "2026-P45", label: "11–15 août 2026", detail: "P45 · 2026" },
  { id: "2026-P44", label: "6–10 août 2026", detail: "P44 · 2026" },
  { id: "2026-P43", label: "1–5 août 2026", detail: "P43 · 2026" },
  { id: "2026-P42", label: "26–31 juillet 2026", detail: "P42 · 2026" },
  { id: "2026-P41", label: "21–25 juillet 2026", detail: "P41 · 2026" },
];

type GalleryMap = { id: string | number; product: Product; label: string; date: string; tone: string; value?: string; imageUrl?: string; thumbnailUrl?: string };

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

function AuthScreen() {
  const [mode, setMode] = useState<"login" | "signup" | "reset">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      const auth = getFirebaseAuth();
      if (!auth) throw new Error("Auth indisponible");
      if (mode === "reset") await sendPasswordResetEmail(auth, email);
      else if (mode === "signup") await createUserWithEmailAndPassword(auth, email, password);
      else await signInWithEmailAndPassword(auth, email, password);
      if (mode === "reset") setMessage("Un lien de réinitialisation a été envoyé.");
    } catch { setMessage("Email ou mot de passe invalide. Vérifiez vos informations."); }
    finally { setBusy(false); }
  }
  return <main className="auth-shell"><div className="auth-card"><div className="brand-symbol"><span>ND</span><i /></div><span className="section-kicker">MÉTÉO BÉNIN · eVIIRS 375 m</span><h1>{mode === "login" ? "Votre espace cartes" : mode === "signup" ? "Créer un compte" : "Mot de passe oublié"}</h1><p>Accédez à vos générations et à votre archive personnelle.</p><form onSubmit={submit}><label htmlFor="auth-email">Adresse email<input id="auth-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@exemple.com" autoComplete="email" /></label>{mode !== "reset" && <label htmlFor="auth-password">Mot de passe<input id="auth-password" type="password" required minLength={6} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="6 caractères minimum" autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>}<button className="auth-submit" disabled={busy}>{busy ? "Veuillez patienter…" : mode === "login" ? "Se connecter" : mode === "signup" ? "Créer mon compte" : "Envoyer le lien"}</button></form>{message && <div className="auth-message">{message}</div>}<div className="auth-links">{mode === "login" && <><button onClick={() => setMode("reset")}>Mot de passe oublié ?</button><button onClick={() => setMode("signup")}>Créer un compte</button></>}{mode !== "login" && <button onClick={() => setMode("login")}>Retour à la connexion</button>}</div></div></main>;
}

function Dashboard({ user }: { user: User }) {
  const [product, setProduct] = useState<Product>("anomaly");
  const [pentade, setPentade] = useState(pentades[0].id);
  const [availablePentades, setAvailablePentades] = useState(pentades);
  const [filter, setFilter] = useState<Filter>("all");
  const [activeMap, setActiveMap] = useState<GalleryMap | null>(null);
  const [jobMap, setJobMap] = useState<GalleryMap | null>(null);
  const [maps, setMaps] = useState<GalleryMap[]>([]);
  const [status, setStatus] = useState<"idle" | "pending" | "processing" | "done" | "error">("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("Préparation du traitement");
  const [toast, setToast] = useState("");
  const [showAgro, setShowAgro] = useState(false);
  const [agroYear, setAgroYear] = useState("2026");
  const [agroMonth, setAgroMonth] = useState("8");
  const [agroDecade, setAgroDecade] = useState("1");
  const [agroView, setAgroView] = useState<"rain" | "observations" | "ewetp" | "exports">("rain");
  const [agroStations, setAgroStations] = useState<Array<{ id: string; name: string; department: string; principal?: boolean }>>([]);
  const [agroStation, setAgroStation] = useState("");
  const [rainRows, setRainRows] = useState<Array<{ station_id: string; jour: number; hauteur_mm?: number }>>([]);
  const [agroRows, setAgroRows] = useState<Array<Record<string, number | string | undefined>>>([]);
  const [ewEtpRows, setEwEtpRows] = useState<Array<{ station_id: string; ew?: number; etp?: number }>>([]);
  const [agroMessage, setAgroMessage] = useState("");
  const [exportAvailability, setExportAvailability] = useState({ network: false, climate: false });
  useEffect(() => { document.title = status === "processing" || status === "pending" ? "⏳ Génération… · Cartes NDVI Bénin" : "Cartes NDVI Bénin"; }, [status]);
  useEffect(() => { if (!toast) return; const timer = window.setTimeout(() => setToast(""), 2200); return () => window.clearTimeout(timer); }, [toast]);
  useEffect(() => { if (!showAgro) return; fetch("/api/agro/stations").then((r) => r.json()).then((data) => { const stations = data.stations ?? []; const principals = stations.filter((s: { principal?: boolean }) => s.principal); setAgroStations(stations); setAgroStation(principals[0]?.id ?? stations[0]?.id ?? ""); if (!stations.length) setAgroMessage(data.error ?? "Aucune station enregistrée"); }).catch(() => setAgroMessage("Impossible de charger les stations enregistrées")); }, [showAgro]);
  const agroFetch = async (path: string, init?: RequestInit) => { const response = await fetch(`/api/agro${path}`, init); const data = await response.json(); if (!response.ok) throw new Error(data.detail ?? data.error ?? "Erreur API agro"); return data; };
  // Le proxy Next.js monte déjà la route worker sur `/agro/*`.
  // Donc on ne doit PAS réajouter un préfixe `/agro` ici.
  const saveRain = async () => {
    try {
      await agroFetch("/pluies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year: Number(agroYear), month: Number(agroMonth), decade: Number(agroDecade), valeurs: rainRows })
      });
      setToast("Pluies enregistrées");
      setAgroMessage("Pluies enregistrées");
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Impossible d'enregistrer les pluies");
      setAgroMessage("Impossible d'enregistrer les pluies");
    }
  };

  const saveObservations = async () => {
    try {
      await agroFetch("/observations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year: Number(agroYear), month: Number(agroMonth), decade: Number(agroDecade), station_id: agroStation, valeurs: agroRows })
      });
      setToast("Observations enregistrées");
      setAgroMessage("Observations enregistrées");
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Impossible d'enregistrer les observations");
      setAgroMessage("Impossible d'enregistrer les observations");
    }
  };
  const daysInMonth = new Date(Number(agroYear), Number(agroMonth), 0).getDate();
  const decadeNumber = Number(agroDecade);
  const firstDay = decadeNumber === 1 ? 1 : decadeNumber === 2 ? 11 : 21;
  const lastDay = decadeNumber === 1 ? 10 : decadeNumber === 2 ? 20 : daysInMonth;
  const days = Array.from({ length: lastDay - firstDay + 1 }, (_, index) => firstDay + index);
  useEffect(() => { if (!showAgro) return; Promise.all([agroFetch(`/pluies?year=${agroYear}&month=${agroMonth}&decade=${agroDecade}`), agroFetch(`/ew-etp?year=${agroYear}&month=${agroMonth}&decade=${agroDecade}`)]).then(([rain, climate]) => setExportAvailability({ network: (rain.valeurs ?? []).length > 0, climate: (climate.valeurs ?? []).length > 0 })).catch(() => setExportAvailability({ network: false, climate: false })); }, [showAgro, agroYear, agroMonth, agroDecade]);
  const updateRain = (station_id: string, jour: number, value: string) => setRainRows((rows) => [...rows.filter((row) => !(row.station_id === station_id && row.jour === jour)), ...(value === "" ? [] : [{ station_id, jour, hauteur_mm: Number(value) }])]);
  const updateAgro = (jour: number, key: string, value: string) => setAgroRows((rows) => { const current = rows.find((row) => row.jour === jour) ?? { jour }; const next = { ...current, [key]: value === "" ? undefined : Number(value) }; return [...rows.filter((row) => row.jour !== jour), next]; });
  useEffect(() => {
    let cancelled = false;
    const loadPentades = () => fetch(`/api/pentades?product=${product}`).then((response) => response.json()).then((data) => {
      if (cancelled || !Array.isArray(data.pentades) || !data.pentades.length) return;
      const next = data.pentades.map((item: { id: string; label: string; year: number; num: number }) => ({ id: item.id, label: item.label, detail: `P${String(item.num).padStart(2, "0")} · ${item.year}` }));
      setAvailablePentades(next); setPentade(next[0].id);
    }).catch(() => setToast("Impossible de charger les pentades"));
    loadPentades();
    return () => { cancelled = true; };
  }, [product]);
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await fetch("/api/jobs", { headers: { Authorization: `Bearer ${await user.getIdToken()}` }, cache: "no-store" });
        const data = await response.json();
        if (!cancelled && response.ok) setMaps((data.jobs ?? []).map((item: { id: string; product: Product; label?: string; pentadeId: string; completedAt?: { _seconds?: number }; imageUrl?: string; thumbnailUrl?: string }) => ({ id: item.id, product: item.product, label: item.label ?? item.pentadeId, date: item.completedAt?._seconds ? new Date(item.completedAt._seconds * 1000).toLocaleDateString("fr-FR") : "Récemment", tone: item.product === "anomaly" ? "olive" : "forest", imageUrl: item.imageUrl, thumbnailUrl: item.thumbnailUrl })));
      } catch { if (!cancelled) setToast("Galerie Firestore indisponible"); }
    };
    load(); const timer = window.setInterval(load, 8000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, []);
  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    const load = async () => { const response = await fetch(`/api/jobs/${jobId}`, { headers: { Authorization: `Bearer ${await user.getIdToken()}` }, cache: "no-store" }); const data = await response.json(); if (cancelled || !response.ok) return; setStatus(data.status ?? "idle"); setProgress(Number(data.progress ?? 0)); setStep(data.step ?? "Préparation du traitement"); setError(data.error ?? ""); if (data.status === "done" && data.imageUrl) setJobMap({ id: data.id ?? jobId, product: data.product ?? product, label: data.label ?? selected.label, date: new Date().toLocaleDateString("fr-FR"), tone: data.product === "anomaly" ? "olive" : "forest", imageUrl: data.imageUrl, thumbnailUrl: data.thumbnailUrl }); };
    load(); const timer = window.setInterval(load, 4000); return () => { cancelled = true; window.clearInterval(timer); };
  }, [jobId]);

  const visibleMaps = useMemo(() => filter === "all" ? maps : maps.filter((item) => item.product === filter), [filter, maps]);
  const selected = availablePentades.find((item) => item.id === pentade) ?? availablePentades[0] ?? pentades[0];
  const previewMap = maps.find((item) => item.product === product && item.label === selected.label) ?? jobMap;

  async function generate() {
    const id = `job-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setJobId(id); setJobMap(null); setStatus("pending"); setError("");
    try {
      const response = await fetch("/api/generate", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${await user.getIdToken()}` }, body: JSON.stringify({ jobId: id, pentadeId: pentade, product, force: false }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "La génération a échoué");
    } catch (generationError) { setError(generationError instanceof Error ? generationError.message : "Erreur de génération"); setStatus("error"); }
  }

  function copyLink() { navigator.clipboard?.writeText("https://res.cloudinary.com/ndvi-benin/anomaly_2026-P44.jpg"); setToast("Lien copié"); }

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand">
        <div className="brand-symbol"><span>ND</span><i /></div>
        <div><div className="brand-name">Météo Bénin</div><div className="brand-sub">Observatoire de la végétation</div></div>
      </div>
      <div className="topbar-meta" style={{ display: "flex" }}><span className="live-dot" /><span className="user-email">{user.email}</span><button className="settings-text-button" onClick={() => setShowAgro(true)}>Paramètres agrométéo</button><button className="logout-button" onClick={() => { const auth = getFirebaseAuth(); if (auth) void signOut(auth); }}>Déconnexion</button></div>
    </header>

    <section className="hero-row">
      <div><div className="eyebrow">PRODUCTION CARTOGRAPHIQUE <span>·</span> BÉNIN</div><h1>Cartes de végétation</h1><p>Générez et consultez les indicateurs NDVI à 375 m, période par période.</p></div>
      <div className="hero-stats"><div><strong>375</strong><span>m résolution</span></div><div><strong>72</strong><span>pentades / an</span></div><div><strong>12</strong><span>départements</span></div></div>
    </section>

    <section className="workspace-grid">
      <div className="generation-card card">
        <div className="card-heading"><div><span className="section-kicker">NOUVELLE CARTE</span><h2>Paramètres de génération</h2></div><span className="secure-pill"><span className="live-dot" /> Source active</span></div>
        <div className="field-block"><label>Produit cartographique</label><div className="product-toggle"><button className={product === "anomaly" ? "active anomaly-active" : ""} onClick={() => setProduct("anomaly")}><span className="toggle-swatch anomaly-swatch" /><span><strong>NDVI anomalie</strong><small>Pourcentage de la moyenne</small></span></button><button className={product === "ndvi" ? "active" : ""} onClick={() => setProduct("ndvi")}><span className="toggle-swatch ndvi-swatch" /><span><strong>NDVI brut</strong><small>Indice de végétation</small></span></button></div></div>
        <div className="field-block"><label htmlFor="pentade">Période d’analyse</label><div className="select-wrap"><Icon name="calendar" size={17} /><select id="pentade" value={pentade} onChange={(event) => setPentade(event.target.value)}>{availablePentades.map((item) => <option key={item.id} value={item.id}>{item.label}  ·  {item.detail}</option>)}</select><span className="select-chevron">⌄</span></div><span className="field-hint">Les données les plus récentes sont proposées en premier.</span></div>
        <button className="generate-button" onClick={generate} disabled={status === "processing" || status === "pending"}><span>{status === "processing" || status === "pending" ? "Génération en cours…" : "Générer la carte"}</span><Icon name="arrow" size={18} /></button>
        <div className={`job-status ${status}`} aria-live="polite">{(status === "idle" || status === "error") && <><span className="status-icon"><Icon name="layers" size={17} /></span><span><strong>{status === "error" ? "Échec de génération" : "Prêt à générer"}</strong><small>{status === "error" ? error : "Le traitement prend généralement 1 à 5 minutes sur Render Free."}</small></span></>}{(status === "processing" || status === "pending") && <><span className="spinner" /><span className="progress-copy"><strong>{status === "pending" ? "Serveur en réveil…" : "Génération en cours"}</strong><small>{step}</small><span className="progress-track"><span style={{ width: `${progress}%` }} /></span></span><b>{progress}%</b></>}{status === "done" && <><span className="status-icon done-icon">✓</span><span><strong>Carte prête</strong><small>{product === "anomaly" ? "NDVI anomalie" : "NDVI brut"} · {selected.label}</small></span><button onClick={() => previewMap && setActiveMap(previewMap)}>Voir</button></>}</div>
      </div>
      <div className="preview-card card"><div className="preview-top"><div><span className="section-kicker">APERÇU DU PRODUIT</span><h2>{product === "anomaly" ? "NDVI anomalie" : "NDVI brut"}</h2></div><span className={`product-badge ${product}`}>{product === "anomaly" ? "ANOMALIE" : "NDVI"}</span></div>{previewMap?.imageUrl ? <img className="real-preview" src={previewMap.imageUrl} alt={`Carte réelle ${product} du Bénin · ${previewMap.label}`} /> : <div className="preview-empty"><Icon name="map" size={26} /><strong>Aucune carte réelle disponible</strong><span>Générez cette période pour afficher le raster USGS découpé sur les limites du Bénin.</span></div>}<div className="preview-caption"><span><Icon name="map" size={15} /> Bénin · {previewMap?.label ?? selected.label}</span><span className="caption-muted">USGS FEWS NET · données réelles uniquement</span></div></div>
    </section>

    <section className="gallery-section"><div className="gallery-heading"><div><div className="eyebrow">ARCHIVE EN TEMPS RÉEL</div><h2>Cartes générées <span>{maps.length}</span></h2></div><div className="filter-tabs"><button className={filter === "all" ? "selected" : ""} onClick={() => setFilter("all")}>Toutes <em>{maps.length}</em></button><button className={filter === "ndvi" ? "selected" : ""} onClick={() => setFilter("ndvi")}>NDVI</button><button className={filter === "anomaly" ? "selected" : ""} onClick={() => setFilter("anomaly")}>Anomalie</button></div></div><div className="gallery-grid">{visibleMaps.length ? visibleMaps.map((item) => <button className="gallery-item" key={item.id} onClick={() => setActiveMap(item)}>{item.thumbnailUrl ? <img className="real-thumb" src={item.thumbnailUrl} alt={`Carte ${item.label}`} /> : <div className="preview-empty"><Icon name="map" size={20} /><span>Aperçu indisponible</span></div>}<div className="gallery-info"><div><span className={`mini-badge ${item.product}`}>{item.product === "anomaly" ? "Anomalie" : "NDVI"}</span><strong>{item.label}</strong></div><span className="gallery-date">{item.date}</span></div></button>) : <div className="empty-gallery"><Icon name="map" size={22} /><strong>Aucune carte générée</strong><span>Choisissez une pentade ci-dessus pour commencer.</span></div>}</div></section>

    <footer className="footer"><span>Source : USGS FEWS NET · eVIIRS 375 m</span><span>Plateforme opérationnelle <span className="live-dot" /></span></footer>
    {showAgro && <div className="lightbox" role="dialog" aria-modal="true" onClick={() => setShowAgro(false)}><div className="lightbox-panel agro-panel" onClick={(event) => event.stopPropagation()}><div className="lightbox-head"><h2>Bulletin agrométéo</h2><button className="icon-button" onClick={() => setShowAgro(false)} aria-label="Fermer"><Icon name="close" /></button></div><div className="agro-period"><label>Année<select value={agroYear} onChange={(event) => setAgroYear(event.target.value)}>{Array.from({ length: 101 }, (_, index) => 2000 + index).map((year) => <option key={year} value={year}>{year}</option>)}</select></label><label>Mois<select value={agroMonth} onChange={(event) => setAgroMonth(event.target.value)}>{["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"].map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></label><label>Décade<select value={agroDecade} onChange={(event) => setAgroDecade(event.target.value)}><option value="1">1ère décade</option><option value="2">2ème décade</option><option value="3">3ème décade</option></select></label></div><nav className="agro-nav"><button className={agroView === "rain" ? "selected" : ""} onClick={() => setAgroView("rain")}>Saisie pluviométrie</button><button className={agroView === "observations" ? "selected" : ""} onClick={() => setAgroView("observations")}>Renseignements agro</button><button className={agroView === "ewetp" ? "selected" : ""} onClick={() => setAgroView("ewetp")}>ew / ETP</button><button className={agroView === "exports" ? "selected" : ""} onClick={() => setAgroView("exports")}>Exports</button></nav>{agroView === "rain" && <><div className="agro-table-wrap"><table className="agro-table"><thead><tr><th>Station</th>{days.map((day) => <th key={day}>J{day}</th>)}<th>NbJP&gt;0</th><th>NbJP&gt;20</th><th>Max</th><th>Total</th></tr></thead><tbody>{agroStations.map((station) => { const values=days.map((day)=>rainRows.find((row)=>row.station_id===station.id&&row.jour===day)?.hauteur_mm); const valid=values.filter((value):value is number=>value!==undefined); return <tr key={station.id}><td>{station.name}</td>{days.map((day)=><td key={day}><input type="number" value={rainRows.find((row)=>row.station_id===station.id&&row.jour===day)?.hauteur_mm??""} onChange={(event)=>updateRain(station.id,day,event.target.value)}/></td>)}<td>{valid.filter((value)=>value>0).length}</td><td>{valid.filter((value)=>value>20).length}</td><td>{valid.length?Math.max(...valid):""}</td><td>{valid.length?valid.reduce((a,b)=>a+b,0):""}</td></tr>})}</tbody></table></div><button className="primary-small" onClick={()=>void saveRain()}>Enregistrer les pluies</button></>}{agroView === "observations" && <><label>Station<select value={agroStation} onChange={(event)=>setAgroStation(event.target.value)}>{agroStations.filter((station)=>station.principal).map((station)=><option key={station.id} value={station.id}>{station.name}</option>)}</select></label><div className="agro-table-wrap"><table className="agro-table"><thead><tr><th>Jour</th><th>Pluie</th><th>T min</th><th>T max</th><th>T moy</th><th>Hum min</th><th>Hum max</th><th>Hum moy</th><th>Insolation</th><th>ETP Bac A</th></tr></thead><tbody>{days.map((day)=>{const row=agroRows.find((item)=>item.jour===day)??{jour:day}; return <tr key={day}><td>{day}</td>{["pluie","temp_min","temp_max","humidite_min","humidite_max","insolation","evapo_bac_a"].map((key)=><td key={key}><input type="number" value={row[key]??""} onChange={(event)=>updateAgro(day,key,event.target.value)}/></td>)}<td>{row.temp_min!==undefined&&row.temp_max!==undefined?(Number(row.temp_min)+Number(row.temp_max))/2:""}</td><td>{row.humidite_min!==undefined&&row.humidite_max!==undefined?0.6*Number(row.humidite_min)+0.4*Number(row.humidite_max):""}</td></tr>})}</tbody></table></div><button className="primary-small" onClick={()=>void saveObservations()}>Enregistrer les observations</button></>}{agroView === "ewetp" && <div className="agro-table-wrap"><table className="agro-table"><thead><tr><th>Station</th><th>Fract. Insol.</th><th>Ray. Global</th><th>H×10</th><th>ew</th><th>ETP</th></tr></thead><tbody>{agroStations.filter((station)=>station.principal).map((station)=><tr key={station.id}><td>{station.name}</td><td></td><td></td><td></td><td><input type="number"/></td><td><input type="number"/></td></tr>)}</tbody></table></div>}{agroView === "exports" && <div className="agro-export-actions"><a aria-disabled={!exportAvailability.network} className={`primary-small ${!exportAvailability.network ? "disabled-export" : ""}`} href={exportAvailability.network ? `/api/agro/export/network.xlsx?year=${agroYear}&month=${agroMonth}&decade=${agroDecade}` : undefined} title={!exportAvailability.network ? "Aucune donnée saisie pour cette décade" : undefined}>Exporter Réseau pluviométrique</a><a aria-disabled={!exportAvailability.climate} className={`primary-small ${!exportAvailability.climate ? "disabled-export" : ""}`} href={exportAvailability.climate ? `/api/agro/export/climate.xlsx?year=${agroYear}&month=${agroMonth}&decade=${agroDecade}` : undefined} title={!exportAvailability.climate ? "Aucune donnée saisie pour cette décade" : undefined}>Exporter Données climatiques</a></div>}{agroMessage&&<p className="settings-intro">{agroMessage}</p>}</div></div>}
    {activeMap && <div className="lightbox" role="dialog" aria-modal="true" aria-label="Visualiseur de carte" onClick={() => setActiveMap(null)}><div className="lightbox-panel" onClick={(event) => event.stopPropagation()}><div className="lightbox-head"><div><span className={`mini-badge ${activeMap.product}`}>{activeMap.product === "anomaly" ? "Anomalie" : "NDVI"}</span><h2>{activeMap.label}</h2></div><button className="icon-button" onClick={() => setActiveMap(null)} aria-label="Fermer"><Icon name="close" /></button></div>{activeMap.imageUrl && <img className="real-map" src={activeMap.imageUrl} alt={`Carte ${activeMap.label}`} />}<div className="lightbox-actions"><button className="secondary-button" onClick={copyLink}><Icon name="copy" size={16} /> Copier le lien</button>{activeMap.imageUrl && <a className="primary-small" href={activeMap.imageUrl} download><Icon name="download" size={16} /> Télécharger JPEG</a>}</div></div></div>}
    {toast && <div className="toast">✓ {toast}</div>}
  </main>;
}

export default function HomePage() {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  useEffect(() => { const auth = getFirebaseAuth(); return auth ? onAuthStateChanged(auth, setUser) : undefined; }, []);
  if (user === undefined) return <main className="auth-shell"><div className="auth-card"><span className="spinner" /></div></main>;
  return user ? <Dashboard user={user} /> : <AuthScreen />;
}
