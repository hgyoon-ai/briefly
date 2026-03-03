import React from 'react';
import '../styles/TodaysSummary.css';

function TodaysSummary({ data, tab = 'ai', showTitle = true, compact = false }) {
  const { highlights, cards } = data;

  const filteredCards = cards.filter(card => card.tab === tab);
  const hasCards = filteredCards.length > 0;

  const EmptyState = () => (
    <div className="empty-issues highlight-empty">
      <div className="empty-icon">✨</div>
      <div className="empty-title">오늘은 소식이 드문 날이에요</div>
      <div className="empty-desc">주간/월간 탭에서 전체 흐름을 확인해 보세요.</div>
    </div>
  );

  return (
    <section className={`todays-summary ${compact ? 'compact' : ''}`.trim()}>
      {showTitle ? <h2 className="section-title">📌 오늘의 요약</h2> : null}

      {/* 3줄 요약 - Highlights */}
      <div className="news-cards-section">
        <h3>핵심 내용</h3>
        <div className={`three-line-summary ${!hasCards ? 'is-empty' : ''}`}>
          {!hasCards ? (
            <EmptyState />
          ) : (
            highlights.bullets.map((bullet, idx) => (
              <div key={idx} className="summary-item">
                <div className="summary-number">{idx + 1}.</div>
                <div className="summary-content">
                  <div className="summary-text">{bullet}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 오늘 소식 카드 */}
      {hasCards && (
        <div className="news-cards-section">
          <h3>오늘의 소식</h3>
          <div className="news-cards">
            {filteredCards.map((card) => {
              const hasLink = Boolean(card.url);
              const CardTag = hasLink ? 'a' : 'div';
              const publishedTime = new Date(card.publishedAt).toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit'
              });

              return (
                <CardTag
                  key={card.id}
                  href={hasLink ? card.url : undefined}
                  target={hasLink ? "_blank" : undefined}
                  rel={hasLink ? "noopener noreferrer" : undefined}
                  className={`news-card ${hasLink ? 'has-link' : ''}`}
                >
                  <div className="card-source">{card.source}</div>
                  {hasLink && (
                    <span className="external-icon" aria-hidden>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14 3h7v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M10 14L21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M21 21H3V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                  )}
                  <div className="card-title">{card.title}</div>
                  <div className="card-summary">
                    {card.summary.map((line, idx) => (
                      <div key={idx} className="summary-line">• {line}</div>
                    ))}
                  </div>
                  <div className="card-footer">
                    <div className="card-why">{card.whyItMatters}</div>
                    <div className="card-topics">
                      {card.topics.map((topic) => (
                        <span key={topic} className="topic-tag">{topic}</span>
                      ))}
                    </div>
                    <div className="card-time-below">{publishedTime}</div>
                  </div>
                </CardTag>
              );
            })}
          </div>
        </div>
      )}

    </section>
  );
}

export default TodaysSummary;
