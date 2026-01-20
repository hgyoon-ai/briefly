import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AdminPage.css';

function AdminPage() {
  const [todayData, setTodayData] = useState(null);
  const [weeklyData, setWeeklyData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // mock 데이터 로드
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}mock/dummy_today.json`).then(res => res.json()),
      fetch(`${import.meta.env.BASE_URL}mock/dummy_7d.json`).then(res => res.json()),
      fetch(`${import.meta.env.BASE_URL}mock/dummy_30d.json`).then(res => res.json())
    ])
      .then(([today, weekly, monthly]) => {
        setTodayData(today);
        setWeeklyData(weekly);
        setMonthlyData(monthly);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load mock data:', err);
        setLoading(false);
      });
  }, []);

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

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>✨ 관리자 페이지</h1>
          <Link to="/" className="back-link" title="홈으로">
            <span>⚡</span>
          </Link>
        </div>
      </header>

      <main className="admin-content">
        {/* 일간 통계 */}
        {todayData && (
          <section className="stats-section">
            <h2>📅 일간</h2>
            <div className="date-label">기준 날짜: {todayData.date}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{todayData.highlights.stats.collected}</div>
                <div className="stat-desc">기사</div>
                {todayData.yesterday && (
                  <ChangeIndicator 
                    current={todayData.highlights.stats.collected} 
                    previous={todayData.yesterday.stats.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{todayData.highlights.stats.deduped}</div>
                <div className="stat-desc">건</div>
                {todayData.yesterday && (
                  <ChangeIndicator 
                    current={todayData.highlights.stats.deduped} 
                    previous={todayData.yesterday.stats.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{todayData.highlights.topTopics.length}</div>
                <div className="stat-desc">개</div>
                {todayData.yesterday && (
                  <ChangeIndicator 
                    current={todayData.highlights.topTopics.length} 
                    previous={todayData.yesterday.stats.uniqueTopics}
                  />
                )}
              </div>
            </div>
          </section>
        )}

        {/* 주간 통계 */}
        {weeklyData && todayData && (
          <section className="stats-section">
            <h2>📊 주간</h2>
            <div className="date-label">기준 기간: {weeklyData.range.from} ~ {weeklyData.range.to}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{weeklyData.kpis.collected}</div>
                <div className="stat-desc">기사</div>
                {weeklyData.previousWeek && (
                  <ChangeIndicator 
                    current={weeklyData.kpis.collected} 
                    previous={weeklyData.previousWeek.kpis.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{weeklyData.kpis.deduped}</div>
                <div className="stat-desc">건</div>
                {weeklyData.previousWeek && (
                  <ChangeIndicator 
                    current={weeklyData.kpis.deduped} 
                    previous={weeklyData.previousWeek.kpis.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{weeklyData.kpis.uniqueTopics}</div>
                <div className="stat-desc">개</div>
                {weeklyData.previousWeek && (
                  <ChangeIndicator 
                    current={weeklyData.kpis.uniqueTopics} 
                    previous={weeklyData.previousWeek.kpis.uniqueTopics}
                  />
                )}
              </div>
            </div>
          </section>
        )}

        {/* 월간 통계 */}
        {monthlyData && weeklyData && (
          <section className="stats-section">
            <h2>📈 월간</h2>
            <div className="date-label">기준 기간: {monthlyData.range.from} ~ {monthlyData.range.to}</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">수집</div>
                <div className="stat-value">{monthlyData.kpis.collected}</div>
                <div className="stat-desc">기사</div>
                {monthlyData.previousMonth && (
                  <ChangeIndicator 
                    current={monthlyData.kpis.collected} 
                    previous={monthlyData.previousMonth.kpis.collected}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">중복 제거</div>
                <div className="stat-value">{monthlyData.kpis.deduped}</div>
                <div className="stat-desc">건</div>
                {monthlyData.previousMonth && (
                  <ChangeIndicator 
                    current={monthlyData.kpis.deduped} 
                    previous={monthlyData.previousMonth.kpis.deduped}
                  />
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">주제</div>
                <div className="stat-value">{monthlyData.kpis.uniqueTopics}</div>
                <div className="stat-desc">개</div>
                {monthlyData.previousMonth && (
                  <ChangeIndicator 
                    current={monthlyData.kpis.uniqueTopics} 
                    previous={monthlyData.previousMonth.kpis.uniqueTopics}
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
