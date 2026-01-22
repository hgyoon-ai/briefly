import React from 'react';
import '../styles/TodaysSummary.css';

function TodaysSummary({ data }) {
  const { highlights, cards } = data;

  // AI 탭만 필터링 (나중에 탭 기능 추가 시 동적으로 변경)
  const aiCards = cards.filter(card => card.tab === 'ai');

  return (
    <section className="todays-summary">
      <h2 className="section-title">📌 오늘의 요약</h2>

      {/* 3줄 요약 - Highlights */}
      <div className="three-line-summary">
        <h3>핵심 내용</h3>
        {highlights.bullets.map((bullet, idx) => (
          <div key={idx} className="summary-item">
            <div className="summary-number">{idx + 1}.</div>
            <div className="summary-content">
              <div className="summary-text">{bullet}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 주요 뉴스 카드 */}
        <div className="news-cards-section">
          <h3>주요 이슈</h3>
          {aiCards.length === 0 ? (
            <div className="empty-issues">
              <div className="empty-icon">✨</div>
              <div className="empty-title">오늘은 수집된 이슈가 없습니다</div>
              <div className="empty-desc">조금 뒤 다시 확인해 주세요. 최신 업데이트를 준비 중이에요.</div>
            </div>
          ) : (
            <div className="news-cards">
              {aiCards.map((card) => (
                <a
                  key={card.id}
                  href={card.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-card"
                >
                  <div className="card-source">{card.source}</div>
                  <span className="external-icon" aria-hidden>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14 3h7v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M10 14L21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M21 21H3V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  <div className="card-title">{card.title}</div>
                  <div className="card-time-below">
                    {new Date(card.publishedAt).toLocaleTimeString('ko-KR', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
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
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>

    </section>
  );
}

export default TodaysSummary;
