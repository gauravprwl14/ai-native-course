import type { ReactNode } from 'react';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

interface RelatedNode {
  id: string;
  label: string;
  href: string;
  tier?: 1 | 2 | 3 | 4;
}

interface ConceptMapProps {
  current: string;        // label of current chapter
  currentHref?: string;   // href of current chapter (for display only)
  related: (RelatedNode | string)[]; // related chapters — strings auto-converted to nodes
}

function toNode(item: RelatedNode | string): RelatedNode {
  if (typeof item === 'string') {
    return {
      id: item,
      label: item.replace(/-/g, ' '),
      href: '/' + item,
      tier: 1,
    };
  }
  return item;
}

const TIER_COLORS: Record<number, string> = {
  1: '#6366f1',
  2: '#10b981',
  3: '#f59e0b',
  4: '#ef4444',
};

// Position nodes in a circle around center
function getNodePosition(index: number, total: number, radius: number): { x: number; y: number } {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}

export default function ConceptMap({ current, related }: ConceptMapProps): ReactNode {
  const nodes = related.map(toNode);
  const cx = 200;
  const cy = 200;
  const radius = 130;
  const viewBox = '0 0 400 400';

  return (
    <div className={styles.container}>
      <svg viewBox={viewBox} className={styles.svg} aria-label={`Concept map for ${current}`}>
        {/* Draw lines from center to each related node */}
        {nodes.map((node, i) => {
          const pos = getNodePosition(i, nodes.length, radius);
          return (
            <line
              key={`line-${node.id}`}
              x1={cx}
              y1={cy}
              x2={cx + pos.x}
              y2={cy + pos.y}
              stroke="var(--ifm-toc-border-color)"
              strokeWidth="1.5"
            />
          );
        })}

        {/* Related nodes */}
        {nodes.map((node, i) => {
          const pos = getNodePosition(i, nodes.length, radius);
          const nx = cx + pos.x;
          const ny = cy + pos.y;
          const color = TIER_COLORS[node.tier ?? 1];

          return (
            <g key={node.id} className={styles.nodeGroup}>
              <circle cx={nx} cy={ny} r={28} fill={`${color}20`} stroke={color} strokeWidth="1.5" />
              <foreignObject x={nx - 26} y={ny - 16} width={52} height={32}>
                <Link
                  to={node.href}
                  className={styles.nodeLink}
                  style={{ color }}
                  title={node.label}
                >
                  {node.label.length > 10 ? node.label.substring(0, 10) + '…' : node.label}
                </Link>
              </foreignObject>
            </g>
          );
        })}

        {/* Center node — current chapter */}
        <circle cx={cx} cy={cy} r={40} fill="#6366f120" stroke="#6366f1" strokeWidth="2.5" />
        <foreignObject x={cx - 38} y={cy - 20} width={76} height={40}>
          <div className={styles.centerLabel}>
            {current.length > 12 ? current.substring(0, 12) + '…' : current}
          </div>
        </foreignObject>
      </svg>

      {/* Legend */}
      <div className={styles.legend}>
        {nodes.map((node) => (
          <Link key={node.id} to={node.href} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: TIER_COLORS[node.tier ?? 1] }} />
            {node.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
