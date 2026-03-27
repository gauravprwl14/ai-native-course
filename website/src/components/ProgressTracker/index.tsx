import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface Chapter {
  id: string;
  title: string;
  tier: 1 | 2 | 3 | 4;
}

interface QuizResult {
  score: number;
  max: number;
  passed: boolean;
  date: string;
}

interface ProgressTrackerProps {
  chapters: Chapter[];
}

function loadResult(chapterId: string): QuizResult | null {
  try {
    const raw = localStorage.getItem(`quiz-${chapterId}`);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const TIER_LABELS = { 1: '🧱 Foundations', 2: '🔧 Builder', 3: '🚀 Advanced', 4: '🏗️ Architect' };

export default function ProgressTracker({ chapters }: ProgressTrackerProps): ReactNode {
  const [results, setResults] = useState<Record<string, QuizResult | null>>({});

  useEffect(() => {
    const loaded: Record<string, QuizResult | null> = {};
    for (const ch of chapters) {
      loaded[ch.id] = loadResult(ch.id);
    }
    setResults(loaded);
  }, [chapters]);

  const passed = chapters.filter((ch) => results[ch.id]?.passed).length;
  const pct = chapters.length > 0 ? Math.round((passed / chapters.length) * 100) : 0;

  const byTier = [1, 2, 3, 4] as const;

  return (
    <div className={styles.tracker}>
      <div className={styles.summary}>
        <span className={styles.summaryText}>{passed} / {chapters.length} chapters passed</span>
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${pct}%` }} />
        </div>
        <span className={styles.pct}>{pct}%</span>
      </div>

      {byTier.map((tier) => {
        const tierChapters = chapters.filter((ch) => ch.tier === tier);
        if (tierChapters.length === 0) return null;
        return (
          <div key={tier} className={styles.tierSection}>
            <h4 className={styles.tierLabel}>{TIER_LABELS[tier]}</h4>
            <div className={styles.chapterList}>
              {tierChapters.map((ch) => {
                const result = results[ch.id];
                return (
                  <span
                    key={ch.id}
                    className={`${styles.chip} ${result?.passed ? styles.chipPassed : result ? styles.chipFailed : styles.chipPending}`}
                    title={result ? `Score: ${result.score}/${result.max}` : 'Not attempted'}
                  >
                    {result?.passed ? '✓' : result ? '✗' : '○'} {ch.title}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
