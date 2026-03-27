import { useState, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface AgentLoopProps {
  steps?: string[];
  animated?: boolean;
  intervalMs?: number;
}

const DEFAULT_STEPS = ['👁️ Observe', '🧠 Think', '⚡ Act'];

const STEP_DESCRIPTIONS: Record<string, string> = {
  '👁️ Observe': 'The agent receives input from the environment — a user message, tool result, or sensor data.',
  '🧠 Think': 'The LLM reasons about the observation, considers available tools, and decides what to do next.',
  '⚡ Act': 'The agent executes an action — calls a tool, writes a response, or updates memory.',
};

export default function AgentLoop({
  steps = DEFAULT_STEPS,
  animated = true,
  intervalMs = 1500,
}: AgentLoopProps): ReactNode {
  const [active, setActive] = useState(0);
  const [running, setRunning] = useState(animated);
  const [isMounted, setIsMounted] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || !running) return;
    intervalRef.current = setInterval(() => {
      setActive((prev) => (prev + 1) % steps.length);
    }, intervalMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running, isMounted, steps.length, intervalMs]);

  function pause() {
    setRunning(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
  }

  function play() {
    setRunning(true);
  }

  function prev() {
    pause();
    setActive((a) => (a - 1 + steps.length) % steps.length);
  }

  function next() {
    pause();
    setActive((a) => (a + 1) % steps.length);
  }

  const activeStep = steps[active];
  const description = STEP_DESCRIPTIONS[activeStep] ?? 'Agent processes this step.';

  return (
    <div className={styles.container}>
      <div className={styles.loop}>
        {steps.map((step, i) => (
          <div key={step} className={styles.stepWrapper}>
            <button
              className={`${styles.step} ${i === active ? styles.stepActive : ''}`}
              onClick={() => { pause(); setActive(i); }}
            >
              {step}
            </button>
            {i < steps.length - 1 && (
              <span className={styles.arrow}>→</span>
            )}
          </div>
        ))}
        <span className={styles.arrowBack}>↩ cycle</span>
      </div>

      <div className={styles.description}>
        <strong>{activeStep}</strong> — {description}
      </div>

      <div className={styles.controls}>
        <button className={styles.ctrlBtn} onClick={prev} title="Previous step">← Prev</button>
        <button className={`${styles.ctrlBtn} ${styles.ctrlPrimary}`} onClick={running ? pause : play}>
          {running ? '⏸ Pause' : '▶ Play'}
        </button>
        <button className={styles.ctrlBtn} onClick={next} title="Next step">Next →</button>
      </div>
    </div>
  );
}
