import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface TokenVisualizerProps {
  text: string;
  model?: string;
}

// Approximate tokenization — splits on whitespace and punctuation
// Real tokenization requires tiktoken (server-side) — this is a visual approximation
function approximateTokens(text: string): string[] {
  if (!text) return [];
  // Split on spaces while keeping punctuation attached to words (rough approximation)
  return text.match(/\S+|\s+/g) ?? [];
}

// Cost per 1M input tokens for each model
const MODEL_COSTS: Record<string, number> = {
  'claude-haiku-4-5-20251001': 0.80,
  'claude-sonnet-4-6': 3.00,
  'claude-opus-4-6': 15.00,
  'gpt-4o': 5.00,
  'gpt-4o-mini': 0.15,
};

const TOKEN_COLORS = [
  '#ddd6fe', // violet
  '#bfdbfe', // blue
  '#bbf7d0', // green
  '#fef08a', // yellow
  '#fed7aa', // orange
  '#fecaca', // red
  '#e9d5ff', // purple
  '#99f6e4', // teal
];

export default function TokenVisualizer({ text, model = 'claude-haiku-4-5-20251001' }: TokenVisualizerProps): ReactNode {
  const tokens = approximateTokens(text);
  const tokenCount = tokens.filter((t) => t.trim().length > 0).length;
  const costPerMillion = MODEL_COSTS[model] ?? 1.00;
  const estimatedCost = ((tokenCount / 1_000_000) * costPerMillion).toFixed(8);

  let colorIndex = 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.stat}>
          <strong>{tokenCount}</strong> tokens
        </span>
        <span className={styles.stat}>
          ~<strong>${estimatedCost}</strong> ({model})
        </span>
        <span className={styles.note}>⚠️ Approximate — browser tokenization</span>
      </div>
      <div className={styles.tokenArea}>
        {tokens.map((token, i) => {
          if (!token.trim()) {
            return <span key={i}>{token}</span>;
          }
          const color = TOKEN_COLORS[colorIndex % TOKEN_COLORS.length];
          colorIndex++;
          return (
            <span key={i} className={styles.token} style={{ backgroundColor: color }} title={`Token ${colorIndex}`}>
              {token}
            </span>
          );
        })}
      </div>
    </div>
  );
}
