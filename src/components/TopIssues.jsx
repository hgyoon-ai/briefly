import React from 'react';

function TopIssues({ title = '주요 이슈', issues, onIssueSelect }) {
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
              <div className="issue-meta">{issue.articleCount}개 관련 소식</div>
            </div>
            <span className="issue-link-icon" aria-hidden>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 3h7v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M10 14L21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 21H3V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default TopIssues;
