import React, { useEffect, useRef } from 'react';
import '../styles/IssueModal.css';

function IssueModal({ issue, onClose }) {
  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);
  const prevFocusRef = useRef(null);

  useEffect(() => {
    if (!issue) {
      return undefined;
    }

    prevFocusRef.current = document.activeElement;
    closeButtonRef.current?.focus();

    const handleKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }

      if (event.key !== 'Tab' || !modalRef.current) {
        return;
      }

      const focusables = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusables.length) {
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('keydown', handleKey);
      if (prevFocusRef.current && typeof prevFocusRef.current.focus === 'function') {
        prevFocusRef.current.focus();
      }
    };
  }, [issue, onClose]);

  if (!issue) {
    return null;
  }

  const related = issue.relatedArticles || [];
  const dialogTitleId = `issue-modal-title-${issue.id || 'current'}`;
  const dialogSummaryId = `issue-modal-summary-${issue.id || 'current'}`;

  return (
    <div className="issue-modal-backdrop" onClick={onClose} role="presentation">
      <div
        ref={modalRef}
        className="issue-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={dialogTitleId}
        aria-describedby={dialogSummaryId}
      >
        <div className="issue-modal-header">
          <div>
            <div id={dialogTitleId} className="issue-modal-title">{issue.title}</div>
            <div className="issue-modal-status">{issue.status}</div>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            className="issue-modal-close"
            onClick={onClose}
            aria-label="모달 닫기"
          >
            ✕
          </button>
        </div>
        <div id={dialogSummaryId} className="issue-modal-summary">{issue.summary}</div>
        <div className="issue-modal-section">주요 소식</div>
        {related.length === 0 ? (
          <div className="issue-modal-empty">관련 소식이 아직 정리되지 않았어요.</div>
        ) : (
          <div className="issue-modal-links">
            {related.slice(0, 3).map((article, idx) => (
              <a
                key={`${article.url}-${idx}`}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="issue-modal-link"
                aria-label={`${article.source || '뉴스'} 기사 새 창에서 열기: ${article.title}`}
              >
                <span className="issue-modal-link-main">
                  <span className="issue-modal-source">{article.source}</span>
                  <span className="issue-modal-link-title">{article.title}</span>
                </span>
                <span className="issue-modal-link-icon" aria-hidden>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 3h7v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M10 14L21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 21H3V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default IssueModal;
