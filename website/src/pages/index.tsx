import type { ReactNode } from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import styles from './index.module.css';

/* ─── Hero ────────────────────────────────────────────────────────────── */
function Hero(): ReactNode {
  return (
    <section className={styles.hero} aria-label="Course introduction">
      <div className={styles.heroBg} aria-hidden="true" />
      <div className={styles.heroInner}>
        <div className={styles.heroBadge}>
          <span className={styles.heroBadgeDot} />
          50 Chapters · 50+ Labs · 500+ Questions
        </div>

        <h1 className={styles.heroTitle}>
          Build AI Systems<br />
          <span className={styles.heroAccent}>That Actually Work</span>
        </h1>

        <p className={styles.heroSubtitle}>
          A depth-first engineering course — from LLM internals to production
          multi-agent systems. No fluff, no toy demos. Real code, real patterns,
          interview-ready outcomes.
        </p>

        <div className={styles.heroActions}>
          <Link className={styles.ctaPrimary} to="/intro">
            Start Learning
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <Link className={styles.ctaSecondary} to="/tier-1-foundations">
            Browse Curriculum
          </Link>
        </div>

        <ul className={styles.heroMeta} aria-label="Course highlights">
          <li>✓ Zero fluff — every chapter has a lab</li>
          <li>✓ Production-grade patterns, not toy examples</li>
          <li>✓ Interview-ready — MCQs + hard problems</li>
        </ul>
      </div>
    </section>
  );
}

/* ─── Stats ───────────────────────────────────────────────────────────── */
const stats = [
  { value: '50',   label: 'Chapters',      sub: 'across 4 tiers' },
  { value: '50+',  label: 'Runnable Labs', sub: 'one per chapter' },
  { value: '500+', label: 'MCQ Questions', sub: 'with explanations' },
  { value: '20+',  label: 'Hard Problems', sub: 'interview-level' },
];

function Stats(): ReactNode {
  return (
    <section className={styles.stats} aria-label="Course statistics">
      {stats.map((s) => (
        <div key={s.label} className={styles.statItem}>
          <span className={styles.statValue}>{s.value}</span>
          <span className={styles.statLabel}>{s.label}</span>
          <span className={styles.statSub}>{s.sub}</span>
        </div>
      ))}
    </section>
  );
}

/* ─── Features ────────────────────────────────────────────────────────── */
const features = [
  {
    icon: '⚡',
    title: 'Lab-first, always',
    body: 'Every concept ships with a runnable Python lab. Clone, code, test — no environment setup required.',
  },
  {
    icon: '🧠',
    title: 'Internals, not wrappers',
    body: 'Understand how transformers, tokenizers, embeddings, and inference engines actually work — not just their APIs.',
  },
  {
    icon: '🏗️',
    title: 'Production patterns',
    body: 'RAG pipelines, agent loops, observability, caching, and LLM gateways — patterns you\'d find at Anthropic, OpenAI, and Google.',
  },
  {
    icon: '🎯',
    title: 'Interview-ready',
    body: '500+ MCQs with full explanations, 20+ elite engineering problems, and architecture deep-dives that prep you for senior AI roles.',
  },
  {
    icon: '📐',
    title: 'Structured progression',
    body: 'Four tiers — Foundations → Builder → Advanced → Architect — each tier gates on real competency, not just completion.',
  },
  {
    icon: '♾️',
    title: 'Evergreen content',
    body: 'Model-agnostic. Patterns work with GPT-4o, Claude, Gemini, and open-source. Built to outlast the hype cycle.',
  },
];

function Features(): ReactNode {
  return (
    <section className={styles.features} aria-labelledby="features-heading">
      <div className={styles.featuresInner}>
        <h2 id="features-heading" className={styles.sectionHeading}>
          Why engineers trust this course
        </h2>
        <p className={styles.sectionSub}>
          Not another "call the API and get a response" tutorial.
        </p>
        <div className={styles.featureGrid}>
          {features.map((f) => (
            <div key={f.title} className={styles.featureCard}>
              <span className={styles.featureIcon} aria-hidden="true">{f.icon}</span>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureBody}>{f.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Curriculum bento ────────────────────────────────────────────────── */
const tiers = [
  {
    num:   '01',
    title: 'Foundations',
    sub:   '8 chapters · ~3 hrs',
    description: 'LLMs, tokens, embeddings, context windows, temperature, inference vs training, multimodal models.',
    skills: ['Call any LLM API', 'Understand context limits', 'Count & estimate tokens'],
    href: '/tier-1-foundations',
    accentVar: '--tier-1-accent',
  },
  {
    num:   '02',
    title: 'Builder',
    sub:   '14 chapters · ~8 hrs',
    description: 'Prompt engineering, RAG pipelines, vector databases, agents, tool use, function calling, streaming.',
    skills: ['Build a RAG system', 'Create an agent loop', 'Ship a streaming API'],
    href: '/tier-2-builder',
    accentVar: '--tier-2-accent',
  },
  {
    num:   '03',
    title: 'Advanced',
    sub:   '16 chapters · ~12 hrs',
    description: 'Multi-agent systems, long-term memory, fine-tuning, evaluation frameworks, safety, observability.',
    skills: ['Design multi-agent systems', 'Fine-tune a model', 'Build an eval pipeline'],
    href: '/tier-3-advanced',
    accentVar: '--tier-3-accent',
  },
  {
    num:   '04',
    title: 'Architect',
    sub:   '12 chapters · ~10 hrs',
    description: 'Production LLM systems, LLM gateways, caching strategies, cost optimization, full capstone project.',
    skills: ['Design for production', 'Optimize cost & latency', 'Complete system capstone'],
    href: '/tier-4-architect',
    accentVar: '--tier-4-accent',
  },
];

function Curriculum(): ReactNode {
  return (
    <section className={styles.curriculum} aria-labelledby="curriculum-heading">
      <div className={styles.curriculumInner}>
        <h2 id="curriculum-heading" className={styles.sectionHeading}>
          Four tiers. One complete path.
        </h2>
        <p className={styles.sectionSub}>
          Start from zero. Graduate as an AI systems architect.
        </p>
        <div className={styles.bentoGrid}>
          {tiers.map((tier) => (
            <Link
              key={tier.num}
              to={tier.href}
              className={styles.bentoCard}
              style={{ '--tier-accent': `var(${tier.accentVar})` } as React.CSSProperties}
              aria-label={`Tier ${tier.num}: ${tier.title}`}
            >
              <div className={styles.bentoCardTop}>
                <span className={styles.tierNum} aria-hidden="true">{tier.num}</span>
                <span className={styles.tierSub}>{tier.sub}</span>
              </div>
              <h3 className={styles.tierTitle}>Tier {tier.num} —<br />{tier.title}</h3>
              <p className={styles.tierDesc}>{tier.description}</p>
              <ul className={styles.tierSkills} aria-label="What you will learn">
                {tier.skills.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              <span className={styles.tierCta} aria-hidden="true">
                Explore tier →
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Final CTA band ──────────────────────────────────────────────────── */
function CTABand(): ReactNode {
  return (
    <section className={styles.ctaBand} aria-labelledby="cta-heading">
      <div className={styles.ctaBandInner}>
        <h2 id="cta-heading" className={styles.ctaBandTitle}>
          Ready to build AI systems<br />
          <span className={styles.heroAccent}>the right way?</span>
        </h2>
        <p className={styles.ctaBandSub}>
          Start with Tier 1 — free, no account required.
        </p>
        <Link className={styles.ctaPrimary} to="/tier-1-foundations/llms">
          Begin Tier 1
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </Link>
      </div>
    </section>
  );
}

/* ─── Page ────────────────────────────────────────────────────────────── */
export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title="Production AI Engineering Course"
      description="A depth-first engineering course covering LLMs, RAG, agents, fine-tuning, and production AI systems. 50 chapters, 50+ labs, 500+ MCQs."
    >
      <Hero />
      <main>
        <Stats />
        <Features />
        <Curriculum />
        <CTABand />
      </main>
    </Layout>
  );
}
