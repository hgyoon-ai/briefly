import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AdminPage.css';
import useMockData from '../hooks/useMockData';

function AdminPage() {
  const [activeTab, setActiveTab] = useState('ai');
  const { today, weekly, monthly, loading, error } = useMockData(activeTab);

  // 변화 계산 함수 (절대값으로 변환)
  const calculateChange = (current, previous) => {
    if (!previous || previous === 0) return 0;
    return current - previous;
  };

  // 변화 표시 컴포넌트
  const ChangeIndicator = ({ current, previous }) => {
    const change = calculateChange(current, previous);
    const isPositive = change > 0;
    const arrow = isPositive ? '▲' : change < 0 ? '▼' : '';
    
    return (
      <div className={`change-indicator ${isPositive ? 'positive' : change < 0 ? 'negative' : 'neutral'}`}>
        <span className="change-arrow">{arrow}</span>
        <span className="change-text">{Math.abs(change)}건</span>
      </div>
    );
  };

  // 최근 업데이트: cards에서 가장 최신 publishedAt 찾기
  const getLastUpdated = () => {
    if (!today || !today.cards || today.cards.length === 0) return '';
    
    // cards의 publishedAt 중 가장 최신(큰) 값 찾기
    const latestCard = today.cards.reduce((latest, card) => {
      return new Date(card.publishedAt) > new Date(latest.publishedAt) ? card : latest;
    });
    
    const date = new Date(latestCard.publishedAt);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}.${month}.${day} ${hours}:${minutes}`;
  };

  const lastUpdated = getLastUpdated();

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (error || !today || !weekly || !monthly) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>✨ 관리자 페이지</h1>
          <Link to="/" className="back-link" title="홈으로">
            <span>✨</span>
          </Link>
        </div>
        {today && (
          <div className="last-updated">최근 업데이트: {lastUpdated}</div>
        )}
      </header>

      <nav className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          🤖 AI
        </button>
        <button
          className={`tab-button ${activeTab === 'semiconductor' ? 'active' : ''}`}
          onClick={() => setActiveTab('semiconductor')}
        >
          🔌 반도체
        </button>
        <button
          className={`tab-button ${activeTab === 'ev' ? 'active' : ''}`}
          onClick={() => setActiveTab('ev')}
        >
          ⚡ 전기차
        </button>
      </nav>

      <main className="admin-content">
        {/* 일간 통계 */}
        {today && (
          <section className="stats-section">
            <h2>📅 일간</h2>
            <div className="date-label">기준 날짜: {today.date}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{today.highlights.stats.collected}</div>
                <div className="stat-desc">기사</div>
                {today.yesterday && (
                  <ChangeIndicator 
                    current={today.highlights.stats.collected} 
                    previous={today.yesterday.stats.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{today.highlights.stats.deduped}</div>
                <div className="stat-desc">건</div>
                {today.yesterday && (
                  <ChangeIndicator 
                    current={today.highlights.stats.deduped} 
                    previous={today.yesterday.stats.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{today.highlights.topTopics.length}</div>
                <div className="stat-desc">개</div>
                {today.yesterday && (
                  <ChangeIndicator 
                    current={today.highlights.topTopics.length} 
                    previous={today.yesterday.stats.uniqueTopics}
                  />
                )}
              </div>
            </div>
          </section>
        )}

        {/* 주간 통계 */}
        {weekly && today && (
          <section className="stats-section">
            <h2>📊 주간</h2>
            <div className="date-label">기준 기간: {weekly.range.from} ~ {weekly.range.to}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{weekly.kpis.collected}</div>
                <div className="stat-desc">기사</div>
                {weekly.previousWeek && (
                  <ChangeIndicator 
                    current={weekly.kpis.collected} 
                    previous={weekly.previousWeek.kpis.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{weekly.kpis.deduped}</div>
                <div className="stat-desc">건</div>
                {weekly.previousWeek && (
                  <ChangeIndicator 
                    current={weekly.kpis.deduped} 
                    previous={weekly.previousWeek.kpis.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{weekly.kpis.uniqueTopics}</div>
                <div className="stat-desc">개</div>
                {weekly.previousWeek && (
                  <ChangeIndicator 
                    current={weekly.kpis.uniqueTopics} 
                    previous={weekly.previousWeek.kpis.uniqueTopics}
                  />
                )}
              </div>
            </div>
          </section>
        )}

        {/* 월간 통계 */}
        {monthly && weekly && (
          <section className="stats-section">
            <h2>📈 월간</h2>
            <div className="date-label">기준 기간: {monthly.range.from} ~ {monthly.range.to}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{monthly.kpis.collected}</div>
                <div className="stat-desc">기사</div>
                {monthly.previousMonth && (
                  <ChangeIndicator 
                    current={monthly.kpis.collected} 
                    previous={monthly.previousMonth.kpis.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{monthly.kpis.deduped}</div>
                <div className="stat-desc">건</div>
                {monthly.previousMonth && (
                  <ChangeIndicator 
                    current={monthly.kpis.deduped} 
                    previous={monthly.previousMonth.kpis.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{monthly.kpis.uniqueTopics}</div>
                <div className="stat-desc">개</div>
                {monthly.previousMonth && (
                  <ChangeIndicator 
                    current={monthly.kpis.uniqueTopics} 
                    previous={monthly.previousMonth.kpis.uniqueTopics}
                  />
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default AdminPage;
