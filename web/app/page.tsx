export default function HomePage() {
  return (
    <main className="page-shell">
      <header className="site-header">
        <div className="brand-mark" aria-hidden="true">NDVI</div>
        <div>
          <h1>Cartes NDVI Bénin</h1>
          <p>eVIIRS 375 m - FEWS NET</p>
        </div>
      </header>
      <section className="panel" aria-labelledby="generation-title">
        <h2 id="generation-title">Générer une carte</h2>
        <p className="muted">Le sélecteur de produit et de pentade sera disponible dans l’étape suivante.</p>
        <div className="status">Worker et interface en cours de configuration.</div>
      </section>
      <section className="panel" aria-labelledby="gallery-title">
        <h2 id="gallery-title">Cartes générées</h2>
        <p className="muted">Aucune carte générée pour l’instant.</p>
      </section>
    </main>
  );
}
