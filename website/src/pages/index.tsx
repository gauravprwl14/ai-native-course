import type { ReactNode } from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import styles from './index.module.css';

function Hero(): ReactNode {
  return (
    <div className={styles.hero}>
      <div className={styles.heroContent}>
        <h1 className={styles.heroTitle}>
          AI-Native Development
        </h1>
        <p className={styles.heroSubtitle}>
          A practical, depth-first course for developers who want to
          build production AI systems — not just call an API.
        </p>
        <div className={styles.heroButtons}>
          <Link className="button button--primary button--lg" to="/intro">
            Start Learning →
          </Link>
          <Link
            className="button button--secondary button--lg"
            href="https://github.com/your-org/ai-native-course"
          >
            View on GitHub
          </Link>
        </div>
      </div>
    </div>
  );
}

const tiers = [
  {
    emoji: '🧱',
    title: 'Tier 1 — Foundations',
    chapters: 8,
    description: 'LLMs, tokens, embeddings, context windows, multimodal. Call any API confidently.',
    href: '/tier-1-foundations',
    color: '#e0e7ff',
    border: '#6366f1',
  },
  {
    emoji: '🔧',
    title: 'Tier 2 — Builder',
    chapters: 14,
    description: 'Prompt engineering, RAG pipelines, vector DBs, agents, tool use, streaming.',
    href: '/tier-2-builder',
    color: '#d1fae5',
    border: '#10b981',
  },
  {
    emoji: '🚀',
    title: 'Tier 3 — Advanced',
    chapters: 16,
    description: 'Multi-agent systems, memory, fine-tuning, evaluation, safety, observability.',
    href: '/tier-3-advanced',
    color: '#fef3c7',
    border: '#f59e0b',
  },
  {
    emoji: '🏗️',
    title: 'Tier 4 — Architect',
    chapters: 12,
    description: 'Production systems, LLM protocols, caching, gateways, and a full capstone.',
    href: '/tier-4-architect',
    color: '#fee2e2',
    border: '#ef4444',
  },
];

function TierGrid(): ReactNode {
  return (
    <section className={styles.tiers}>
      <h2>Course Structure</h2>
      <div className={styles.tierGrid}>
        {tiers.map((tier) => (
          <Link
            key={tier.title}
            to={tier.href}
            className={styles.tierCard}
            style={{ '--tier-color': tier.color, '--tier-border': tier.border } as React.CSSProperties}
          >
            <span className={styles.tierEmoji}>{tier.emoji}</span>
            <h3>{tier.title}</h3>
            <p className={styles.tierChapters}>{tier.chapters} chapters</p>
            <p>{tier.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

const stats = [
  { value: '50', label: 'Chapters' },
  { value: '50+', label: 'Runnable Labs' },
  { value: '500+', label: 'MCQ Questions' },
  { value: '20+', label: 'Elite Problems' },
];

function Stats(): ReactNode {
  return (
    <section className={styles.stats}>
      {stats.map((s) => (
        <div key={s.label} className={styles.statItem}>
          <span className={styles.statValue}>{s.value}</span>
          <span className={styles.statLabel}>{s.label}</span>
        </div>
      ))}
    </section>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <Hero />
      <main>
        <Stats />
        <TierGrid />
      </main>
    </Layout>
  );
}
