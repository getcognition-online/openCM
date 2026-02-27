import fs from 'fs';
import path from 'path';
import "./../globals.css";

export default function ModelsPage() {
  const modelsDir = path.join(process.cwd(), 'models');
  const filenames = fs.readdirSync(modelsDir);
  
  const models = filenames.filter(f => f.endsWith('.json')).map(filename => {
    const filePath = path.join(modelsDir, filename);
    const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    return {
      id: filename.replace('.opencm.json', ''),
      name: content.metadata?.name || filename,
      description: content.metadata?.description || "A validated causal model in OpenCM format.",
      domain: content.metadata?.domain || "General"
    };
  });

  return (
    <main className="container" style={{ padding: '6rem 2rem' }}>
      <nav style={{ marginBottom: '3rem' }}>
        <a href="/" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>← Back to Home</a>
      </nav>

      <header style={{ marginBottom: '4rem' }}>
        <h1 className="premium-gradient-text">Model Explorer</h1>
        <p>A library of 50+ validated, standard-ready Structural Causal Models.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '2rem' }}>
        {models.map(model => (
          <div key={model.id} className="glass-card" style={{ textAlign: 'left', display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>{model.domain}</span>
            <h3 style={{ marginBottom: '1rem' }}>{model.name}</h3>
            <p style={{ fontSize: '1rem', flex: '1', marginBottom: '1.5rem', opacity: '0.8' }}>{model.description}</p>
            <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.8rem' }}>
              <span className="glass-card" style={{ padding: '4px 12px', borderRadius: '20px' }}>.opencm.json</span>
              <span className="glass-card" style={{ padding: '4px 12px', borderRadius: '20px' }}>CC0</span>
            </div>
          </div>
        ))}
      </div>

      <footer style={{ marginTop: '6rem', textAlign: 'center', opacity: '0.5' }}>
        <p>© 2026 OpenCM Standard | Building the future of Causal AI.</p>
      </footer>
    </main>
  );
}
