import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AdminPage.css';
import useMockData from '../hooks/useMockData';
import useMarketAdminData from '../hooks/useMarketAdminData';
import useRunHistory from '../hooks/useRunHistory';
import useDeveloperRadar from '../hooks/useDeveloperRadar';
import { ADMIN_ICON } from '../constants/ui';

const STORAGE_KEY = 'briefly.adminTabs';
const DEFAULT_STATE = {
  mode: 'securities',
  briefingTab: 'ai',
  marketTab: 'securities-ai'
};

const loadAdminState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_STATE;
    const parsed = JSON.parse(raw);
    const mode =
      parsed.mode === 'industry' || parsed.mode === 'developer' || parsed.mode === 'securities'
        ? parsed.mode
        : parsed.mode === 'briefing'
          ? 'industry'
          : parsed.mode === 'market'
            ? 'securities'
            : 'securities';
    return {
      mode,
      briefingTab:
        parsed.briefingTab === 'finance' || parsed.briefingTab === 'semiconductor' || parsed.briefingTab === 'ev'
          ? parsed.briefingTab
          : 'ai',
      marketTab:
        parsed.marketTab === 'securities-updates' || parsed.marketTab === 'securities-ai'
          ? parsed.marketTab
          : parsed.marketTab === 'securities'
            ? 'securities-ai'
            : 'securities-ai'
    };
  } catch (error) {
    return DEFAULT_STATE;
  }
};

function AdminPage() {
  const [adminState, setAdminState] = useState(loadAdminState);
  const { mode, briefingTab, marketTab } = adminState;
  const { today, weekly, monthly, loading, error } = useMockData(briefingTab);
  const marketData = useMarketAdminData(marketTab);
  const briefingRuns = useRunHistory('briefing/run_history.json');
  const marketRuns = useRunHistory(`market/${marketTab}/run_history.json`);
  const developerData = useDeveloperRadar();
  const developerRuns = useRunHistory('developer/run_history.json');

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(adminState));
  }, [adminState]);

  const activeTab = useMemo(() => {
    if (mode === 'securities') return marketTab;
    if (mode === 'industry') return briefingTab;
    return 'developer';
  }, [mode, marketTab, briefingTab]);

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
  const latestBriefingRun = briefingRuns.history?.[0];
  const latestDeveloperRun = developerRuns.history?.[0];
  const latestMarketRun = marketRuns.history?.[0];

  const formatDateTime = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('ko-KR');
  };

  if (mode === 'industry' && loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (mode === 'industry' && (error || !today || !weekly || !monthly)) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>🛠️ 관리자 페이지</h1>
          <Link to="/" className="back-link" title="홈으로">
            <span>{ADMIN_ICON}</span>
          </Link>
        </div>
        {mode === 'industry' && (
          <div className="last-updated">
            최근 실행: {latestBriefingRun?.ts ? new Date(latestBriefingRun.ts).toLocaleString('ko-KR') : '-'}
            {today && lastUpdated ? ` · 카드 최신: ${lastUpdated}` : ''}
          </div>
        )}
        {mode === 'securities' && (
          <div className="last-updated">
            최근 실행: {latestMarketRun?.ts ? new Date(latestMarketRun.ts).toLocaleString('ko-KR') : '-'}
            {marketData.index?.lastUpdated ? ` · 카드 최신: ${formatDateTime(marketData.index.lastUpdated)}` : ''}
          </div>
        )}
        {mode === 'developer' && (
          <div className="last-updated">
            최근 실행: {latestDeveloperRun?.ts ? new Date(latestDeveloperRun.ts).toLocaleString('ko-KR') : '-'}
            {developerData.daily?.date ? ` · 카드 최신: ${formatDateTime(developerData.daily.date)}` : ''}
          </div>
        )}
      </header>

      <nav className="admin-nav-shell">
        <div className="admin-mode-row">
          <div className="admin-mode-label">모드</div>
          <div className="admin-mode-switch">
            <button
              className={`tab-button mode-button ${mode === 'securities' ? 'active' : ''}`}
              title="증권사"
              aria-label="증권사"
              onClick={() => {
                setAdminState((prev) => ({ ...prev, mode: 'securities' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                🏦
              </span>
              <span className="mode-text">증권사</span>
            </button>
            <button
              className={`tab-button mode-button ${mode === 'industry' ? 'active' : ''}`}
              title="산업"
              aria-label="산업"
              onClick={() => {
                setAdminState((prev) => ({ ...prev, mode: 'industry' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                🏭
              </span>
              <span className="mode-text">산업</span>
            </button>
            <button
              className={`tab-button mode-button ${mode === 'developer' ? 'active' : ''}`}
              title="개발"
              aria-label="개발"
              onClick={() => {
                setAdminState((prev) => ({ ...prev, mode: 'developer' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                🧭
              </span>
              <span className="mode-text">개발</span>
            </button>
          </div>
          <div className="admin-mode-status">
            {mode === 'securities' ? '증권사' : mode === 'industry' ? '산업' : '개발'}
          </div>
        </div>
        <div className="admin-nav-divider" />
        <div className="admin-tabs-row">
          {mode === 'securities' ? (
            <>
              <button
                className={`tab-button ${activeTab === 'securities-ai' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, marketTab: 'securities-ai' }));
                }}
              >
                🏦 증권AI
              </button>
              <button
                className={`tab-button ${activeTab === 'securities-updates' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, marketTab: 'securities-updates' }));
                }}
              >
                🧩 증권 업데이트
              </button>
            </>
          ) : mode === 'industry' ? (
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
                className={`tab-button ${activeTab === 'finance' ? 'active' : ''}`}
                onClick={() => {
                  setAdminState((prev) => ({ ...prev, briefingTab: 'finance' }));
                }}
              >
                💼 금융/규제
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
          ) : (
            <button className="tab-button disabled" disabled>
              🌐 글로벌 레이더
              <span className="coming-soon">Daily</span>
            </button>
          )}
        </div>
      </nav>

      <main className="admin-content">
        {mode === 'industry' ? (
          <>
            <RunHistoryPanel
              title="🧾 최근 7회 실행(브리핑)"
              runs={briefingRuns.history}
              loading={briefingRuns.loading}
              error={briefingRuns.error}
              kind="briefing"
            />
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
        ) : mode === 'securities' ? (
          <MarketAdminPanel marketData={marketData} marketRuns={marketRuns} dataset={marketTab} />
        ) : (
          <DeveloperAdminPanel radar={developerData} />
        )}
      </main>
    </div>
  );
}

function RunHistoryPanel({ title, runs, loading, error, kind }) {
  const formatNumber = (value) => {
    if (typeof value !== 'number' || Number.isNaN(value)) return '-';
    return value.toLocaleString('ko-KR');
  };

  const getLatestNumber = (series) => {
    for (let i = series.length - 1; i >= 0; i -= 1) {
      const value = series[i];
      if (typeof value === 'number' && !Number.isNaN(value)) return value;
    }
    return null;
  };

  const buildSeries = (metricGetter) => {
    if (!Array.isArray(runs) || runs.length === 0) return [];

    // runs are stored newest-first; sparkline should read left->right (oldest->newest)
    return runs
      .slice(0, 7)
      .slice()
      .reverse()
      .map((run) => {
        try {
          const value = metricGetter(run);
          const asNumber = typeof value === 'number' ? value : Number(value);
          return Number.isFinite(asNumber) ? asNumber : null;
        } catch (e) {
          return null;
        }
      });
  };

  const Sparkline = ({ series, stroke, ariaLabel }) => {
    const width = 180;
    const height = 24;
    const padX = 2;
    const padY = 3;

    const points = series.length ? series : [];
    const numeric = points.filter((v) => typeof v === 'number' && !Number.isNaN(v));
    const min = numeric.length ? Math.min(...numeric) : 0;
    const max = numeric.length ? Math.max(...numeric) : 0;
    const range = max - min;

    const stepX = points.length > 1 ? (width - padX * 2) / (points.length - 1) : 0;

    const toY = (v) => {
      if (typeof v !== 'number' || Number.isNaN(v)) return height - padY;
      if (range === 0) return Math.round(height / 2);
      const ratio = (v - min) / range;
      return Math.round(height - padY - ratio * (height - padY * 2));
    };

    const coords = points
      .map((v, idx) => {
        const x = Math.round(padX + idx * stepX);
        const y = toY(v);
        return `${x},${y}`;
      })
      .join(' ');

    return (
      <svg
        className="admin-spark-svg"
        viewBox={`0 0 ${width} ${height}`}
        width={width}
        height={height}
        role="img"
        aria-label={ariaLabel}
        preserveAspectRatio="none"
      >
        <polyline
          fill="none"
          stroke={stroke}
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
          points={coords}
          opacity={numeric.length ? 1 : 0.35}
        />
      </svg>
    );
  };

  if (loading) {
    return (
      <section className="stats-section">
        <h2>{title}</h2>
        <div className="admin-empty">불러오는 중...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="stats-section">
        <h2>{title}</h2>
        <div className="admin-empty">실행 로그를 불러올 수 없습니다.</div>
      </section>
    );
  }

  if (!runs || runs.length === 0) {
    return (
      <section className="stats-section">
        <h2>{title}</h2>
        <div className="admin-empty">아직 기록이 없습니다.</div>
      </section>
    );
  }

  const metrics =
    kind === 'briefing'
      ? [
          {
            key: 'raw',
            label: 'raw',
            stroke: '#ff6b9d',
            getter: (run) => run?.pipeline?.rawTotal
          },
          {
            key: 'dedupe',
            label: 'dedupe',
            stroke: '#ffa500',
            getter: (run) => run?.pipeline?.dedupedSelected ?? run?.pipeline?.deduped
          },
          {
            key: 'llm',
            label: 'llm(item)',
            stroke: '#4a90e2',
            getter: (run) => run?.llm?.itemCalls
          }
        ]
      : [
          {
            key: 'raw',
            label: 'raw',
            stroke: '#ff6b9d',
            getter: (run) => run?.filters?.rawItems
          },
          {
            key: 'cand',
            label: 'cand',
            stroke: '#ffa500',
            getter: (run) => run?.filters?.candidates
          },
          {
            key: 'llm',
            label: 'llm(sent)',
            stroke: '#4a90e2',
            getter: (run) => run?.llm?.sent
          }
        ];

  const seriesByMetric = Object.fromEntries(metrics.map((m) => [m.key, buildSeries(m.getter)]));

  return (
    <section className="stats-section">
      <h2>{title}</h2>
      <div className="admin-run-trends" aria-label="최근 7회 추이">
        {metrics.map((metric) => {
          const series = seriesByMetric[metric.key] || [];
          const latest = getLatestNumber(series);
          return (
            <div key={metric.key} className="admin-spark-row">
              <div className="admin-spark-label">{metric.label}</div>
              <Sparkline
                series={series}
                stroke={metric.stroke}
                ariaLabel={`${metric.label} trend: ${series.map((v) => (typeof v === 'number' ? v : '-')).join(', ')}`}
              />
              <div className="admin-spark-value">{formatNumber(latest)}</div>
            </div>
          );
        })}
      </div>
      <div className="admin-list">
        {runs.slice(0, 7).map((run) => {
          const ts = run?.ts ? new Date(run.ts).toLocaleString('ko-KR') : '-';
          const errorsCount = Array.isArray(run?.errors) ? run.errors.length : 0;
          const selectedTabs = Array.isArray(run?.selectedTabs) ? run.selectedTabs : null;

          let summary = '';
          if (kind === 'briefing') {
            summary = `raw ${run?.pipeline?.rawTotal ?? '-'} → dedupe ${run?.pipeline?.dedupedSelected ?? run?.pipeline?.deduped ?? '-'} → enrich ${run?.pipeline?.enriched ?? '-'}`;
          } else {
            summary = `raw ${run?.filters?.rawItems ?? '-'} → cand ${run?.filters?.candidates ?? '-'} → kept ${run?.output?.kept ?? '-'}`;
          }

          return (
            <div key={run.id || ts} className="admin-list-item compact">
              <div className="admin-list-meta">
                <span>{ts}</span>
                {selectedTabs ? <span>tabs {selectedTabs.join(',')}</span> : null}
                <span>errors {errorsCount}</span>
              </div>
              <div className="admin-list-title">{summary}</div>
              {kind === 'briefing' ? (
                <div className="admin-list-summary">
                  RSS {run?.sources?.rss?.total ?? '-'} · HF {run?.sources?.hf?.total ?? '-'} · HN {run?.sources?.hn?.total ?? '-'} · LLM(item) {run?.llm?.itemCalls ?? '-'}
                </div>
              ) : (
                <div className="admin-list-summary">
                  App Store fetched {run?.sources?.app_store?.fetchedOk ?? '-'} · DART matched {run?.sources?.dart?.matched ?? (run?.sources?.dart?.skipped ? 'skipped' : '-')} · News entries {run?.sources?.news?.entriesFetched ?? '-'} · LLM sent {run?.llm?.sent ?? '-'} (cache {run?.llm?.cacheHit ?? '-'})
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function MarketAdminPanel({ marketData, marketRuns, dataset }) {
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
      <RunHistoryPanel
        title="🧾 최근 7회 실행(마켓)"
        runs={marketRuns.history}
        loading={marketRuns.loading}
        error={marketRuns.error}
        kind="market"
      />
      <section className="stats-section">
        <h2>
          {dataset === 'securities-updates' ? '🧩 증권 업데이트' : '🏦 증권사 AI 데이터'}
        </h2>
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

function DeveloperAdminPanel({ radar }) {
  const { daily, loading, error } = radar;

  if (loading) {
    return <div className="loading">개발 레이더 데이터를 불러오는 중...</div>;
  }

  if (error || !daily) {
    return <div className="error">개발 레이더 데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <>
      <section className="stats-section">
        <h2>🧭 개발 레이더</h2>
        <div className="date-label">최근 업데이트: {daily.date || '-'}</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">감지 엔티티</div>
            <div className="stat-value">{daily.kpis?.clusters ?? 0}</div>
            <div className="stat-desc">개</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">활성 소스</div>
            <div className="stat-value">{daily.kpis?.sources ?? 0}</div>
            <div className="stat-desc">개</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">신규 감지</div>
            <div className="stat-value">{daily.kpis?.new ?? 0}</div>
            <div className="stat-desc">개</div>
          </div>
        </div>
      </section>
      <section className="stats-section">
        <h2>🧪 상위 엔티티</h2>
        {!daily.clusters?.length ? (
          <div className="admin-empty">아직 감지된 엔티티가 없습니다.</div>
        ) : (
          <div className="admin-list">
            {daily.clusters.slice(0, 6).map((cluster) => (
              <div key={cluster.id} className="admin-list-item compact">
                <div className="admin-list-meta">
                  <span>{cluster.section || 'trending'}</span>
                  <span>{cluster.status || 'ONGOING'}</span>
                  <span>score {cluster.score ?? '-'}</span>
                </div>
                <div className="admin-list-title">{cluster.name}</div>
                <div className="admin-list-summary">{cluster.oneLiner}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

export default AdminPage;
