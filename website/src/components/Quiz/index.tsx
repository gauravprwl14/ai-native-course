import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface Question {
  id: string;
  text: string;
  options: string[];
  correct: number;
  explanation: string;
  points?: number;
}

interface QuizProps {
  questions: Question[];
  chapterId: string;
  passMark?: number;
}

type AnswerState = {
  selected: number | null;
  revealed: boolean;
};

function saveResult(chapterId: string, score: number, max: number, passMark: number) {
  try {
    localStorage.setItem(
      `quiz-${chapterId}`,
      JSON.stringify({ score, max, passed: (score / max) * 100 >= passMark, date: new Date().toISOString() })
    );
  } catch {
    // localStorage may be unavailable in SSR
  }
}

export default function Quiz({ questions, chapterId, passMark = 70 }: QuizProps): ReactNode {
  const [answers, setAnswers] = useState<AnswerState[]>(
    questions.map(() => ({ selected: null, revealed: false }))
  );
  const [submitted, setSubmitted] = useState(false);

  const allAnswered = answers.every((a) => a.revealed);
  const totalPoints = questions.reduce((sum, q) => sum + (q.points ?? 1), 0);
  const earnedPoints = answers.reduce((sum, a, i) => {
    if (a.revealed && a.selected === questions[i].correct) {
      return sum + (questions[i].points ?? 1);
    }
    return sum;
  }, 0);
  const percentage = totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0;
  const passed = percentage >= passMark;

  function selectOption(qi: number, optionIdx: number) {
    if (answers[qi].revealed) return;
    setAnswers((prev) =>
      prev.map((a, i) => (i === qi ? { selected: optionIdx, revealed: true } : a))
    );
  }

  function retake() {
    setAnswers(questions.map(() => ({ selected: null, revealed: false })));
    setSubmitted(false);
  }

  useEffect(() => {
    if (allAnswered && !submitted) {
      setSubmitted(true);
      saveResult(chapterId, earnedPoints, totalPoints, passMark);
    }
  }, [allAnswered, submitted, chapterId, earnedPoints, totalPoints, passMark]);

  return (
    <div className={styles.quizContainer}>
      {questions.map((q, qi) => {
        const ans = answers[qi];
        const isCorrect = ans.revealed && ans.selected === q.correct;
        const pointLabel = q.points && q.points > 1 ? ` (${q.points}pts)` : '';

        return (
          <div key={q.id} className={styles.question}>
            <p className={styles.questionText}>
              <strong>Q{qi + 1}{pointLabel}:</strong> {q.text}
            </p>
            <div className={styles.options}>
              {q.options.map((opt, oi) => {
                let optClass = styles.option;
                if (ans.revealed) {
                  if (oi === q.correct) optClass = `${styles.option} ${styles.correct}`;
                  else if (oi === ans.selected) optClass = `${styles.option} ${styles.incorrect}`;
                } else if (ans.selected === oi) {
                  optClass = `${styles.option} ${styles.selected}`;
                }
                return (
                  <button key={oi} className={optClass} onClick={() => selectOption(qi, oi)}>
                    {opt}
                  </button>
                );
              })}
            </div>
            {ans.revealed && (
              <div className={`${styles.explanation} ${isCorrect ? styles.explanationCorrect : styles.explanationIncorrect}`}>
                {isCorrect ? '✅ Correct!' : `❌ Incorrect. Correct answer: ${q.options[q.correct]}`}
                <br />
                <span>{q.explanation}</span>
              </div>
            )}
          </div>
        );
      })}

      {allAnswered && (
        <div className={styles.scoreBox}>
          <div className={styles.scoreNumber}>
            {earnedPoints}/{totalPoints} pts ({percentage}%)
          </div>
          <div className={passed ? styles.passed : styles.failed}>
            {passed ? '🎉 Passed!' : `Not yet — need ${passMark}% to pass`}
          </div>
          <button className={styles.retakeBtn} onClick={retake}>
            Retake Quiz
          </button>
        </div>
      )}
    </div>
  );
}
