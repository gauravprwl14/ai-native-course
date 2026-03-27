import { useState } from 'react';
import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface ArchDiagramProps {
  title?: string;
  description?: string;
  children: ReactNode;  // The Mermaid code block or SVG content
}

export default function ArchDiagram({ title, description, children }: ArchDiagramProps): ReactNode {
  const [zoomed, setZoomed] = useState(false);

  return (
    <>
      <div className={styles.wrapper}>
        {title && <div className={styles.title}>{title}</div>}
        {description && <div className={styles.description}>{description}</div>}
        <div className={styles.diagramArea}>
          {children}
        </div>
        <button className={styles.zoomBtn} onClick={() => setZoomed(true)} title="Expand diagram">
          ⤢ Expand
        </button>
      </div>

      {zoomed && (
        <div className={styles.overlay} onClick={() => setZoomed(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            {title && <div className={styles.modalTitle}>{title}</div>}
            <div className={styles.modalDiagram}>{children}</div>
            <button className={styles.closeBtn} onClick={() => setZoomed(false)}>✕ Close</button>
          </div>
        </div>
      )}
    </>
  );
}
