import React, { useEffect } from 'react';
import '../styles/IssueModal.css';

function IssueModal({ issue, onClose }) {
  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  if (!issue) {
    return null;
  }

  const related = issue.relatedArticles || [];

  return (
    <div className="issue-modal-backdrop" onClick={onClose} role="presentation">
      <div className="issue-modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <div className="issue-modal-header">
          <div>
            <div className="issue-modal-title">{issue.title}</div>
            <div className="issue-modal-status">{issue.status}</div>
          </div>
          <button type="button" className="issue-modal-close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="issue-modal-summary">{issue.summary}</div>
        <div className="issue-modal-section">주요 기사</div>
        {related.length === 0 ? (
          <div className="issue-modal-empty">관련 기사가 아직 정리되지 않았어요.</div>
        ) : (
          <div className="issue-modal-links">
            {related.slice(0, 3).map((article, idx) => (
              <a
                key={`${article.url}-${idx}`}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="issue-modal-link"
              >
                <span className="issue-modal-source">({article.source})</span>
                <span className="issue-modal-link-title">{article.title}</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default IssueModal;
