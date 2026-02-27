import Image from "next/image";
import "./globals.css";

export default function Home() {
  return (
    <main>
      <section className="hero-section">
        {/* Hero Visual Mockup - We'll reference the generated image */}
        <div className="hero-visual">
          <Image 
            src="/hero_visual.png" 
            alt="Structural Causal Model Visualization" 
            fill
            priority
            style={{ objectFit: 'cover' }}
          />
        </div>

        <div className="container">
          <h1 className="premium-gradient-text">OpenCM 1.0</h1>
          <p>The Universal Interchange Standard for Causal AI.</p>
          <h2>Causal AI — and We’re Giving It Away</h2>
          
          <div style={{ marginTop: '3rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <a href="/spec" className="glass-card" style={{ padding: '1rem 2rem', textDecoration: 'none', color: 'inherit' }}>Read the Spec</a>
            <a href="/models" className="glass-card" style={{ padding: '1rem 2rem', textDecoration: 'none', color: 'inherit' }}>Explore Models</a>
          </div>
        </div>
      </section>

      <section id="mission" style={{ padding: '8rem 2rem' }}>
        <div className="container">
          <div className="glass-card">
            <h2 style={{ marginBottom: '1.5rem' }}>The Infrastructure Gap in Causal AI</h2>
            <p style={{ textAlign: 'left', margin: '0' }}>
              The year is 2026. Causal AI is finally having its moment. After decades of Judea Pearl’s pioneering work on causal inference and structural causal models (SCMs), enterprises are waking up to a fundamental truth: correlation is cheap, causation is priceless.
              <br /><br />
              But causal inference has no portable model format. OpenCM does for causal inference what ONNX did for neural networks: it makes causal models portable, versionable, composable, and transparent.
            </p>
          </div>
        </div>
      </section>

      <section id="features" style={{ padding: '4rem 2rem' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
            <div className="glass-card">
              <h3>Model Registries</h3>
              <p style={{ fontSize: '1rem' }}>Maintain validated causal models—Porter’s Five Forces, PESTLE, and more. Load instantly into your engine.</p>
            </div>
            <div className="glass-card">
              <h3>The Lensing Engine</h3>
              <p style={{ fontSize: '1rem' }}>Treat models like interchangeable reasoning overlays. Swap causal worldviews as easy as changing camera lenses.</p>
            </div>
            <div className="glass-card">
              <h3>Standardized JSON</h3>
              <p style={{ fontSize: '1rem' }}>Language-agnostic specification for variables, edges, structural equations, and explicit assumptions.</p>
            </div>
          </div>
        </div>
      </section>

      <footer style={{ padding: '4rem 2rem', textAlign: 'center', opacity: '0.6' }}>
        <p style={{ fontSize: '0.9rem' }}>
          Dedicated to the Public Domain under CC0 1.0 Universal. <br />
          Built by Cognition Universal Intelligence.
        </p>
      </footer>
    </main>
  );
}
