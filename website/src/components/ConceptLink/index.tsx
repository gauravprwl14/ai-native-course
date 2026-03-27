import type { ReactNode } from 'react';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

interface ConceptLinkProps {
  to: string;       // doc path e.g. "/tier-2-builder/14-rag-core"
  label: string;    // display text e.g. "RAG — Core Concept"
  tier?: 1 | 2 | 3 | 4;
}

const TIER_EMOJI = { 1: '🧱', 2: '🔧', 3: '🚀', 4: '🏗️' };

export default function ConceptLink({ to, label, tier }: ConceptLinkProps): ReactNode {
  return (
    <Link to={to} className={styles.link}>
      {tier && <span className={styles.tier}>{TIER_EMOJI[tier]}</span>}
      {label}
      <span className={styles.arrow}>→</span>
    </Link>
  );
}
