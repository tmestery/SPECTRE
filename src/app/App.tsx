export function App() {
  return (
    <div className="shell">
      <header className="banner">
        <h1>SPECTRE</h1>
        <p>GitHub repo audit crew — Phase 1</p>
      </header>
      <main className="grid">
        <section>
          <h2>Agent Chat</h2>
          <p className="placeholder">Connect WebSocket to stream agent messages.</p>
        </section>
        <section>
          <h2>Findings Timeline</h2>
          <p className="placeholder">Run: python -m spectre.cli run --repo owner/repo --scope scopes/spectre.yaml</p>
        </section>
      </main>
    </div>
  );
}
