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
  current: string;
  currentHref?: string;
  related: (RelatedNode | string)[];
}

// Complete slug → { path, tier } registry for all 50 chapters + common aliases
const CHAPTER_REGISTRY: Record<string, { path: string; tier: 1 | 2 | 3 | 4; label?: string }> = {
  // Tier 1 — Foundations
  'llms':                  { path: '/tier-1-foundations/llms', tier: 1, label: 'LLMs' },
  'tokens':                { path: '/tier-1-foundations/tokens', tier: 1 },
  'context-window':        { path: '/tier-1-foundations/context-window', tier: 1 },
  'temperature':           { path: '/tier-1-foundations/temperature', tier: 1 },
  'temperature-sampling':  { path: '/tier-1-foundations/temperature', tier: 1, label: 'temperature' },
  'embeddings':            { path: '/tier-1-foundations/embeddings', tier: 1 },
  'inference-vs-training': { path: '/tier-1-foundations/inference-vs-training', tier: 1 },
  'foundation-models':     { path: '/tier-1-foundations/foundation-vs-finetuned', tier: 1, label: 'foundation models' },
  'foundation-vs-finetuned': { path: '/tier-1-foundations/foundation-vs-finetuned', tier: 1 },
  'multimodal':            { path: '/tier-1-foundations/multimodal', tier: 1 },

  // Tier 2 — Builder
  'zero-few-shot':         { path: '/tier-2-builder/zero-few-shot', tier: 2 },
  'prompting':             { path: '/tier-2-builder/zero-few-shot', tier: 2 },
  'chain-of-thought':      { path: '/tier-2-builder/chain-of-thought', tier: 2 },
  'system-prompts':        { path: '/tier-2-builder/system-prompts', tier: 2 },
  'structured-output':     { path: '/tier-2-builder/structured-output', tier: 2 },
  'role-meta-prompting':   { path: '/tier-2-builder/role-meta-prompting', tier: 2 },
  'rag':                   { path: '/tier-2-builder/rag-core', tier: 2, label: 'RAG' },
  'rag-core':              { path: '/tier-2-builder/rag-core', tier: 2, label: 'RAG core' },
  'vector-databases':      { path: '/tier-2-builder/vector-databases', tier: 2 },
  'semantic-search':       { path: '/tier-2-builder/vector-databases', tier: 2, label: 'semantic search' },
  'chunking':              { path: '/tier-2-builder/chunking', tier: 2 },
  'hybrid-search':         { path: '/tier-2-builder/hybrid-search', tier: 2 },
  're-ranking':            { path: '/tier-2-builder/reranking', tier: 2, label: 're-ranking' },
  'reranking':             { path: '/tier-2-builder/reranking', tier: 2 },
  'tool-use':              { path: '/tier-2-builder/tool-use', tier: 2 },
  'function-calling':      { path: '/tier-2-builder/tool-use', tier: 2, label: 'function calling' },
  'agentic-loop':          { path: '/tier-2-builder/agentic-loop', tier: 2 },
  'agents':                { path: '/tier-2-builder/ai-agent', tier: 2 },
  'ai-agent':              { path: '/tier-2-builder/ai-agent', tier: 2 },
  'streaming':             { path: '/tier-2-builder/streaming', tier: 2 },

  // Tier 3 — Advanced
  'planning':              { path: '/tier-3-advanced/planning', tier: 3 },
  'multi-agent':           { path: '/tier-3-advanced/multi-agent', tier: 3 },
  'memory':                { path: '/tier-3-advanced/agent-memory', tier: 3 },
  'agent-memory':          { path: '/tier-3-advanced/agent-memory', tier: 3 },
  'reflection':            { path: '/tier-3-advanced/reflection', tier: 3 },
  'agent-handoff':         { path: '/tier-3-advanced/agent-handoff', tier: 3 },
  'hitl':                  { path: '/tier-3-advanced/hitl', tier: 3, label: 'HITL' },
  'fine-tuning':           { path: '/tier-3-advanced/fine-tuning', tier: 3 },
  'lora':                  { path: '/tier-3-advanced/lora', tier: 3, label: 'LoRA' },
  'rlhf':                  { path: '/tier-3-advanced/rlhf-dpo', tier: 3, label: 'RLHF / DPO' },
  'rlhf-dpo':              { path: '/tier-3-advanced/rlhf-dpo', tier: 3, label: 'RLHF / DPO' },
  'evals':                 { path: '/tier-3-advanced/evals', tier: 3 },
  'llm-as-judge':          { path: '/tier-3-advanced/llm-as-judge', tier: 3 },
  'hallucination-detection': { path: '/tier-3-advanced/hallucination', tier: 3 },
  'tracing':               { path: '/tier-3-advanced/tracing', tier: 3 },
  'guardrails':            { path: '/tier-3-advanced/guardrails', tier: 3 },
  'prompt-injection':      { path: '/tier-3-advanced/prompt-injection', tier: 3 },
  'pii-handling':          { path: '/tier-3-advanced/pii-handling', tier: 3, label: 'PII handling' },
  'agentic-workflows':     { path: '/tier-3-advanced/planning', tier: 3, label: 'agentic workflows' },

  // Tier 4 — Architect
  'llm-apis':              { path: '/tier-4-architect/llm-apis', tier: 4, label: 'LLM APIs' },
  'model-selection':       { path: '/tier-4-architect/model-selection', tier: 4 },
  'mcp':                   { path: '/tier-4-architect/mcp', tier: 4, label: 'MCP' },
  'a2a-acp':               { path: '/tier-4-architect/a2a-acp', tier: 4, label: 'A2A / ACP' },
  'llm-hosting':           { path: '/tier-4-architect/llm-hosting', tier: 4 },
  'llm-caching':           { path: '/tier-4-architect/llm-caching', tier: 4 },
  'latency-optimization':  { path: '/tier-4-architect/latency-optimization', tier: 4 },
  'ai-gateway':            { path: '/tier-4-architect/ai-gateway', tier: 4 },
  'graphrag':              { path: '/tier-4-architect/graphrag', tier: 4, label: 'GraphRAG' },
  'durable-workflows':     { path: '/tier-4-architect/durable-workflows', tier: 4 },
  'computer-use':          { path: '/tier-4-architect/computer-use', tier: 4 },
  'capstone':              { path: '/tier-4-architect/capstone', tier: 4 },
};

function toNode(item: RelatedNode | string): RelatedNode {
  if (typeof item === 'string') {
    const entry = CHAPTER_REGISTRY[item];
    const label = entry?.label ?? item.replace(/-/g, ' ');
    return {
      id: item,
      label,
      href: entry?.path ?? '#',
      tier: entry?.tier ?? 1,
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

        <circle cx={cx} cy={cy} r={40} fill="#6366f120" stroke="#6366f1" strokeWidth="2.5" />
        <foreignObject x={cx - 38} y={cy - 20} width={76} height={40}>
          <div className={styles.centerLabel}>
            {current.length > 12 ? current.substring(0, 12) + '…' : current}
          </div>
        </foreignObject>
      </svg>

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
