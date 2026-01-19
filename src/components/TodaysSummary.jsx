import React from 'react';
import '../styles/TodaysSummary.css';

function TodaysSummary({ data }) {
  const { highlights, cards } = data;

  // AI 탭만 필터링 (나중에 탭 기능 추가 시 동적으로 변경)
  const aiCards = cards.filter(card => card.tab === 'ai');

  return (
    <section className="todays-summary">
      <h2 className="section-title">📌 오늘의 요약</h2>

      {/* 하이라이트 카드 */}
      <div className="highlights">
        <div className="highlight-card">
          <div className="highlight-label">수집</div>
          <div className="highlight-value">{highlights.stats.collected}</div>
          <div className="highlight-desc">기사</div>
        </div>
        <div className="highlight-card">
          <div className="highlight-label">중복 제거</div>
          <div className="highlight-value">{highlights.stats.deduped}</div>
          <div className="highlight-desc">건</div>
        </div>
        <div className="highlight-card">
          <div className="highlight-label">주제</div>
          <div className="highlight-value">{highlights.topTopics.length}</div>
          <div className="highlight-desc">개</div>
        </div>
      </div>

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
        <h3>주요 뉴스</h3>
        <div className="news-cards">
          {aiCards.map((card) => (
            <a
              key={card.id}
              href={card.url}
              target="_blank"
              rel="noopener noreferrer"
              className="news-card"
            >
              <div className="card-header">
                <div className="card-source">{card.source}</div>
                <div className="card-time">
                  {new Date(card.publishedAt).toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
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
              </div>
            </a>
          ))}
        </div>
      </div>

    </section>
  );
}

export default TodaysSummary;
