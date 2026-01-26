import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AdminPage.css';
import useMockData from '../hooks/useMockData';
import useMarketAdminData from '../hooks/useMarketAdminData';
import { ADMIN_ICON } from '../constants/ui';

const STORAGE_KEY = 'briefly.adminTabs';
const DEFAULT_STATE = {
  mode: 'market',
  briefingTab: 'ai',
  marketTab: 'securities'
};

const loadAdminState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_STATE;
    const parsed = JSON.parse(raw);
    return {
      mode: parsed.mode === 'briefing' ? 'briefing' : 'market',
      briefingTab:
        parsed.briefingTab === 'semiconductor' || parsed.briefingTab === 'ev'
          ? parsed.briefingTab
          : 'ai',
      marketTab: parsed.marketTab === 'securities' ? parsed.marketTab : 'securities'
    };
  } catch (error) {
    return DEFAULT_STATE;
  }
};

function AdminPage() {
  const [adminState, setAdminState] = useState(loadAdminState);
  const { mode, briefingTab, marketTab } = adminState;
  const { today, weekly, monthly, loading, error } = useMockData(briefingTab);
  const marketData = useMarketAdminData();

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(adminState));
  }, [adminState]);

  const activeTab = useMemo(
    () => (mode === 'market' ? marketTab : briefingTab),
    [mode, marketTab, briefingTab]
  );

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

  if (mode === 'briefing' && loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (mode === 'briefing' && (error || !today || !weekly || !monthly)) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>✨ 관리자 페이지</h1>
          <Link to="/" className="back-link" title="홈으로">
            <span>{ADMIN_ICON}</span>
          </Link>
        </div>
        {mode === 'briefing' && today && (
          <div className="last-updated">최근 업데이트: {lastUpdated}</div>
        )}
      </header>

      <nav className="admin-nav-shell">
        <div className="admin-mode-row">
          <div className="admin-mode-label">모드</div>
          <div className="admin-mode-switch">
            <button
              className={`tab-button mode-button ${mode === 'market' ? 'active' : ''}`}
              title="마켓"
              aria-label="마켓"
              onClick={() => {
                setAdminState((prev) => ({ ...prev, mode: 'market' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                🧭
              </span>
              <span className="mode-text">마켓</span>
            </button>
            <button
              className={`tab-button mode-button ${mode === 'briefing' ? 'active' : ''}`}
              title="브리핑"
              aria-label="브리핑"
              onClick={() => {
                setAdminState((prev) => ({ ...prev, mode: 'briefing' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                📌
              </span>
              <span className="mode-text">브리핑</span>
            </button>
          </div>
          <div className="admin-mode-status">{mode === 'market' ? '마켓' : '브리핑'}</div>
        </div>
        <div className="admin-nav-divider" />
        <div className="admin-tabs-row">
          {mode === 'market' ? (
            <button
              className={`tab-button ${activeTab === 'securities' ? 'active' : ''}`}
              onClick={() => {
                setAdminState((prev) => ({ ...prev, marketTab: 'securities' }));
              }}
            >
              🏦 증권사 AI
            </button>
          ) : (
            <>
              <button
                className={`tab-button ${activeTab === 'ai' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, briefingTab: 'ai' }));
                }}
              >
                🤖 AI
              </button>
              <button
                className={`tab-button ${activeTab === 'semiconductor' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, briefingTab: 'semiconductor' }));
                }}
              >
                🔌 반도체
              </button>
              <button
                className={`tab-button ${activeTab === 'ev' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, briefingTab: 'ev' }));
                }}
              >
                ⚡ 전기차
              </button>
            </>
          )}
        </div>
      </nav>

      <main className="admin-content">
        {mode === 'briefing' ? (
          <>
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
          </>
        ) : (
          <MarketAdminPanel marketData={marketData} />
        )}
      </main>
    </div>
  );
}

function MarketAdminPanel({ marketData }) {
  const { index, events, selectedMonth, setSelectedMonth, loading, error } = marketData;

  const sortedEvents = useMemo(() => {
    return events
      .slice()
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [events]);

  const qualityStats = useMemo(() => {
    const qualityByMonth = index?.qualityByMonth || {};
    const fromIndex = selectedMonth ? qualityByMonth[selectedMonth] : null;
    if (fromIndex) {
      return {
        total: fromIndex.total ?? events.length,
        missingLink: fromIndex.missingLink ?? 0,
        missingSummary: fromIndex.missingSummary ?? 0,
        missingType: fromIndex.missingType ?? 0,
        missingArea: fromIndex.missingArea ?? 0
      };
    }

    const stats = {
      total: events.length,
      missingLink: 0,
      missingSummary: 0,
      missingType: 0,
      missingArea: 0
    };

    events.forEach((event) => {
      if (!event.sources?.[0]?.url) stats.missingLink += 1;
      if (!event.oneLiner) stats.missingSummary += 1;
      if (!event.type) stats.missingType += 1;
      if (!event.areas || event.areas.length === 0) stats.missingArea += 1;
    });

    return stats;
  }, [index, selectedMonth, events]);

  const qualityIssues = useMemo(() => {
    const issues = {
      missingLink: [],
      missingSummary: [],
      missingType: [],
      missingArea: []
    };

    events.forEach((event) => {
      if (!event.sources?.[0]?.url) issues.missingLink.push(event);
      if (!event.oneLiner) issues.missingSummary.push(event);
      if (!event.type) issues.missingType.push(event);
      if (!event.areas || event.areas.length === 0) issues.missingArea.push(event);
    });

    return issues;
  }, [events]);

  const totalIssues = useMemo(() => {
    return (
      qualityIssues.missingLink.length +
      qualityIssues.missingSummary.length +
      qualityIssues.missingType.length +
      qualityIssues.missingArea.length
    );
  }, [qualityIssues]);

  if (loading) {
    return <div className="loading">마켓 데이터를 불러오는 중...</div>;
  }

  if (error || !index) {
    return <div className="error">마켓 데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <>
      <section className="stats-section">
        <h2>🏦 증권사 AI 데이터</h2>
        <div className="date-label">최근 업데이트: {index.lastUpdated || '-'}</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">보관 월</div>
            <div className="stat-value">{index.months?.length || 0}</div>
            <div className="stat-desc">개월</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">누적 이벤트</div>
            <div className="stat-value">{index.counts?.total || 0}</div>
            <div className="stat-desc">건</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">최근 30일</div>
            <div className="stat-value">{index.counts?.last30d || 0}</div>
            <div className="stat-desc">건</div>
          </div>
        </div>
      </section>

      <section className="stats-section">
        <div className="admin-section-header">
          <h2>🧪 데이터 품질</h2>
          <div className="admin-month-select">
            <label htmlFor="market-month">월 선택</label>
            <select
              id="market-month"
              value={selectedMonth || ''}
              onChange={(event) => setSelectedMonth(event.target.value)}
            >
              {(index.months || []).map((month) => (
                <option key={month} value={month}>
                  {month}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">링크 누락</div>
            <div className="stat-value">{qualityStats.missingLink}</div>
            <div className="stat-desc">건</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">요약 누락</div>
            <div className="stat-value">{qualityStats.missingSummary}</div>
            <div className="stat-desc">건</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">유형 누락</div>
            <div className="stat-value">{qualityStats.missingType}</div>
            <div className="stat-desc">건</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">영역 누락</div>
            <div className="stat-value">{qualityStats.missingArea}</div>
            <div className="stat-desc">건</div>
          </div>
        </div>
      </section>

      <section className="stats-section">
        <h2>🔎 품질 이슈</h2>
        {totalIssues === 0 ? (
          <div className="admin-empty">이슈가 없습니다.</div>
        ) : (
          <div className="admin-issue-grid">
            <div className="admin-issue-card">
              <div className="admin-issue-title">링크 누락</div>
              <div className="admin-issue-count">{qualityIssues.missingLink.length}건</div>
              <div className="admin-list">
                {qualityIssues.missingLink.map((event) => (
                  <div key={event.id} className="admin-list-item compact">
                    <div className="admin-list-meta">
                      <span>{event.date}</span>
                      <span>{event.company}</span>
                    </div>
                    <div className="admin-list-title">{event.title}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="admin-issue-card">
              <div className="admin-issue-title">요약 누락</div>
              <div className="admin-issue-count">{qualityIssues.missingSummary.length}건</div>
              <div className="admin-list">
                {qualityIssues.missingSummary.map((event) => (
                  <div key={event.id} className="admin-list-item compact">
                    <div className="admin-list-meta">
                      <span>{event.date}</span>
                      <span>{event.company}</span>
                    </div>
                    <div className="admin-list-title">{event.title}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="admin-issue-card">
              <div className="admin-issue-title">유형 누락</div>
              <div className="admin-issue-count">{qualityIssues.missingType.length}건</div>
              <div className="admin-list">
                {qualityIssues.missingType.map((event) => (
                  <div key={event.id} className="admin-list-item compact">
                    <div className="admin-list-meta">
                      <span>{event.date}</span>
                      <span>{event.company}</span>
                    </div>
                    <div className="admin-list-title">{event.title}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="admin-issue-card">
              <div className="admin-issue-title">영역 누락</div>
              <div className="admin-issue-count">{qualityIssues.missingArea.length}건</div>
              <div className="admin-list">
                {qualityIssues.missingArea.map((event) => (
                  <div key={event.id} className="admin-list-item compact">
                    <div className="admin-list-meta">
                      <span>{event.date}</span>
                      <span>{event.company}</span>
                    </div>
                    <div className="admin-list-title">{event.title}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>
    </>
  );
}

export default AdminPage;
