import React from 'react';

function TopIssues({ title = '주요 소식', issues, onIssueSelect }) {
  if (!issues || issues.length === 0) {
    return null;
  }

  return (
    <div className="top-issues-section">
      <h3>{title}</h3>
      <div className="issues-list">
        {issues.map((issue, idx) => (
          <button
            key={issue.id}
            type="button"
            className="issue-card"
            onClick={() => onIssueSelect && onIssueSelect(issue)}
          >
            <span className="issue-more-icon" aria-hidden>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="1.8"/>
                <path d="M16 16L20 20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </span>
            <div className="issue-rank">#{idx + 1}</div>
            <div className="issue-content">
              <div className="issue-title">
                {issue.title}
                {issue.status && (
                  <span className={`issue-status issue-status-${issue.status.toLowerCase()}`}>
                    {issue.status}
                  </span>
                )}
              </div>
              <div className="issue-summary">{issue.summary}</div>
              <div className="issue-meta-row">
                <div className="issue-meta">{issue.articleCount}개 관련 소식</div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default TopIssues;
