import fs from 'fs';
import path from 'path';
import "./../globals.css";

export default function SpecPage() {
  const specPath = path.join(process.cwd(), 'docs', 'spec.md');
  const specContent = fs.readFileSync(specPath, 'utf8');

  // Basic markdown-to-html transformation logic (simplified for the monster SEO site)
  // We'll replace headers and lists with clean semantic HTML
  const lines = specContent.split('\n');
  const renderedContent = lines.map((line, index) => {
    if (line.startsWith('# ')) return <h1 key={index} className="premium-gradient-text" style={{ marginTop: '2rem' }}>{line.replace('# ', '')}</h1>;
    if (line.startsWith('## ')) return <h2 key={index} style={{ marginTop: '2.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>{line.replace('## ', '')}</h2>;
    if (line.startsWith('### ')) return <h3 key={index} style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>{line.replace('### ', '')}</h3>;
    if (line.startsWith('* ') || line.startsWith('- ')) return <li key={index} style={{ marginLeft: '1.5rem', color: 'rgba(255,255,255,0.8)' }}>{line.substring(2)}</li>;
    if (line.trim() === '---') return <hr key={index} style={{ margin: '3rem 0', opacity: '0.2' }} />;
    if (line.trim() === '') return <br key={index} />;
    return <p key={index} style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'rgba(255,255,255,0.9)' }}>{line}</p>;
  });

  return (
    <main className="container" style={{ padding: '6rem 2rem' }}>
      <nav style={{ marginBottom: '3rem' }}>
        <a href="/" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>← Back to Home</a>
      </nav>
      
      <div className="glass-card" style={{ padding: '4rem', textAlign: 'left' }}>
        {renderedContent}
      </div>
      
      <footer style={{ marginTop: '4rem', textAlign: 'center', opacity: '0.5' }}>
        <p>© 2026 OpenCM Standard | CC0 Public Domain</p>
      </footer>
    </main>
  );
}
