import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenCM 1.0 | The Universal Standard for Causal AI",
  description: "OpenCM 1.0 is the first open, language-agnostic, JSON-based specification for Structural Causal Models (SCMs). Bringing portability and transparency to Causal AI.",
  keywords: ["Causal AI", "Structural Causal Models", "SCM", "OpenCM", "Judea Pearl", "Causal Inference", "Machine Learning Standards"],
  authors: [{ name: "Jamie Nixx", url: "https://getcognition.online" }],
  openGraph: {
    title: "OpenCM 1.0 | The Universal Standard for Causal AI",
    description: "Bringing portability, composability, and transparency to Structural Causal Models.",
    url: "https://opencm.info",
    siteName: "OpenCM",
    images: [
      {
        url: "/hero_visual.png",
        width: 1200,
        height: 630,
        alt: "OpenCM Causal Model Visualization",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenCM 1.0 | The Universal Standard for Causal AI",
    description: "The interchangeable reasoning overlays for Causal AI.",
    images: ["/hero_visual.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "OpenCM 1.0",
    "description": "JSON-based interchange standard for Structural Causal Models.",
    "applicationCategory": "AI Standard",
    "operatingSystem": "All",
    "author": {
      "@type": "Person",
      "name": "Jamie Nixx"
    },
    "license": "https://creativecommons.org/publicdomain/zero/1.0/"
  };

  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
