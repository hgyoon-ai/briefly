import React, { useEffect, useMemo, useState } from 'react';
import useSecuritiesAIMarket from '../hooks/useSecuritiesAIMarket';
import '../styles/SecuritiesAIMarket.css';

const TYPE_OPTIONS = ['전체', '제품/기능', '제휴/협업', '운영/시스템', '대외/인사이트'];
const AREA_OPTIONS = ['전체', '리스크/컴플', '고객/상담', '투자/리서치', '거래/브로커리지', '자산관리(WM)'];
const PERIOD_OPTIONS = [
  { label: '최근 30일', value: '30d' },
  { label: '최근 90일', value: '90d' },
  { label: '전체', value: 'all' }
];

const formatDate = (dateString) =>
  new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });

const matchesSearch = (event, keyword) => {
  if (!keyword) return true;
  const value = keyword.toLowerCase();
  return [
    event.title,
    event.oneLiner,
    event.company,
    ...(event.tags || [])
  ]
    .filter(Boolean)
    .some((text) => text.toLowerCase().includes(value));
};

const withinPeriod = (eventDate, baseDate, period) => {
  if (!baseDate || period === 'all') return true;
  const cutoffDays = period === '30d' ? 30 : 90;
  const cutoff = new Date(baseDate);
  cutoff.setDate(cutoff.getDate() - cutoffDays);
  return new Date(eventDate) >= cutoff;
};

const mapTypeGroup = (value) => {
  switch (value) {
    case '출시':
      return '제품/기능';
    case '제휴':
      return '제휴/협업';
    case '시스템':
      return '운영/시스템';
    case '규제':
    case '특허':
    case '리서치':
    case '채용':
      return '대외/인사이트';
    default:
      return value || '대외/인사이트';
  }
};

const mapAreaGroup = (value) => {
  switch (value) {
    case '리스크':
    case 'AML':
      return '리스크/컴플';
    case '상담':
      return '고객/상담';
    case '리서치':
      return '투자/리서치';
    case '트레이딩':
    case '브로커리지':
      return '거래/브로커리지';
    case 'WM':
      return '자산관리(WM)';
    default:
      return value || '투자/리서치';
  }
};

const mapAreaGroups = (values) => {
  if (!values || values.length === 0) return [];
  return Array.from(new Set(values.map(mapAreaGroup)));
};

const AREA_LANES = ['리스크/컴플', '고객/상담', '투자/리서치', '거래/브로커리지', '자산관리(WM)'];
const TYPE_COLORS = {
  '제품/기능': '#ff6b9d',
  '제휴/협업': '#ffa500',
  '운영/시스템': '#4ecdc4',
  '대외/인사이트': '#6a5acd'
};
const TYPE_KEYS = {
  '제품/기능': 'product',
  '제휴/협업': 'partner',
  '운영/시스템': 'ops',
  '대외/인사이트': 'external'
};

const toDateOnly = (value) => {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
};

const daysBetween = (from, to) => {
  const diff = toDateOnly(to).getTime() - toDateOnly(from).getTime();
  return Math.max(0, Math.round(diff / (1000 * 60 * 60 * 24)));
};

const median = (values) => {
  if (!values.length) return 0;
  const sorted = values.slice().sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return Math.round((sorted[mid - 1] + sorted[mid]) / 2);
  }
  return sorted[mid];
};

const addMonths = (date, months) => {
  const copy = new Date(date);
  copy.setMonth(copy.getMonth() + months);
  return copy;
};

const formatMonth = (date) => {
  const year = String(date.getFullYear()).slice(-2);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `${year}.${month}`;
};

const formatShortDate = (date) =>
  date.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' });

const openSource = (url) => {
  if (!url) return;
  window.open(url, '_blank', 'noopener,noreferrer');
};

const handleCardKeyDown = (event, url) => {
  if (!url) return;
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    openSource(url);
  }
};

function SecuritiesAIMarket() {
  const { index, events, loading, error, lastUpdated } = useSecuritiesAIMarket();
  const [search, setSearch] = useState('');
  const [timelineCompany, setTimelineCompany] = useState('전체');
  const [analysisCompany, setAnalysisCompany] = useState('');
  const [type, setType] = useState('전체');
  const [area, setArea] = useState('전체');
  const [period, setPeriod] = useState('30d');
  const [viewMode, setViewMode] = useState('timeline');
  const [analysisFiltersOpen, setAnalysisFiltersOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [activeTypes, setActiveTypes] = useState({
    product: true,
    partner: true,
    ops: true,
    external: true
  });

  const companyOptions = useMemo(() => {
    const base = index?.companies || [];
    return ['전체', ...base];
  }, [index]);

  const baseEvents = useMemo(() => {
    const baseDate = lastUpdated;
    return events.filter((event) => {
      const eventTypeGroup = mapTypeGroup(event.type);
      const eventAreaGroups = mapAreaGroups(event.areas || []);
      if (type !== '전체' && eventTypeGroup !== type) return false;
      if (area !== '전체' && !eventAreaGroups.includes(area)) return false;
      if (!matchesSearch(event, search)) return false;
      if (!withinPeriod(event.date, baseDate, period)) return false;
      return true;
    });
  }, [events, type, area, search, period, lastUpdated]);

  const timelineEvents = useMemo(() => {
    return baseEvents.filter((event) => {
      if (timelineCompany !== '전체' && event.company !== timelineCompany) return false;
      return true;
    });
  }, [baseEvents, timelineCompany]);

  const analysisEvents = useMemo(() => {
    return baseEvents.filter((event) => {
      if (!analysisCompany) return false;
      return event.company === analysisCompany;
    });
  }, [baseEvents, analysisCompany]);

  const analysisPoints = useMemo(() => {
    return analysisEvents.map((event) => {
      const typeGroup = mapTypeGroup(event.type);
      const areaGroups = mapAreaGroups(event.areas || []);
      const areaGroup = areaGroups[0] || '투자/리서치';
      return {
        ...event,
        typeGroup,
        areaGroup,
        dateObj: toDateOnly(event.date)
      };
    });
  }, [analysisEvents]);

  const timelineRange = useMemo(() => {
    if (analysisPoints.length === 0) {
      return null;
    }
    if (period === 'all') {
      const end = lastUpdated ? toDateOnly(lastUpdated) : new Date();
      const start = addMonths(end, -12);
      return { start, end };
    }
    const dates = analysisPoints.map((event) => event.dateObj.getTime());
    const maxDate = new Date(Math.max(...dates));
    const end = lastUpdated ? toDateOnly(lastUpdated) : maxDate;
    const start = new Date(end);
    start.setDate(start.getDate() - (period === '30d' ? 29 : 89));
    return { start, end };
  }, [analysisPoints, period, lastUpdated]);

  const analysisPointsInRange = useMemo(() => {
    if (!timelineRange) return [];
    return analysisPoints.filter(
      (event) => event.dateObj >= timelineRange.start && event.dateObj <= timelineRange.end
    );
  }, [analysisPoints, timelineRange]);

  const analysisKpis = useMemo(() => {
    if (analysisPointsInRange.length === 0) {
      return {
        total: 0,
        lastDate: null,
        daysSinceLast: null,
        medianGap: 0,
        maxGap: 0
      };
    }
    const sorted = analysisPointsInRange
      .slice()
      .sort((a, b) => b.dateObj.getTime() - a.dateObj.getTime());
    const lastDate = sorted[0].dateObj;
    const gaps = [];
    for (let i = 0; i < sorted.length - 1; i += 1) {
      gaps.push(daysBetween(sorted[i + 1].dateObj, sorted[i].dateObj));
    }
    return {
      total: analysisPointsInRange.length,
      lastDate,
      daysSinceLast: daysBetween(lastDate, lastUpdated || new Date()),
      medianGap: median(gaps),
      maxGap: gaps.length ? Math.max(...gaps) : 0
    };
  }, [analysisPointsInRange, lastUpdated]);

  const typeDistribution = useMemo(() => {
    const counts = TYPE_OPTIONS.filter((item) => item !== '전체').reduce((acc, item) => {
      acc[item] = 0;
      return acc;
    }, {});
    analysisPointsInRange.forEach((event) => {
      counts[event.typeGroup] = (counts[event.typeGroup] || 0) + 1;
    });
    return counts;
  }, [analysisPointsInRange]);

  const areaDistribution = useMemo(() => {
    const counts = AREA_LANES.reduce((acc, item) => {
      acc[item] = 0;
      return acc;
    }, {});
    analysisPointsInRange.forEach((event) => {
      counts[event.areaGroup] = (counts[event.areaGroup] || 0) + 1;
    });
    return counts;
  }, [analysisPointsInRange]);

  const timelineLayout = useMemo(() => {
    if (!timelineRange) return null;
    const padding = 24;
    const totalDays = Math.max(1, daysBetween(timelineRange.start, timelineRange.end));
    const viewWidth =
      period === 'all'
        ? 960
        : Math.max(520, totalDays * 10 + padding * 2);
    const height = 140;
    return { padding, viewWidth, height, totalDays };
  }, [timelineRange, period]);

  const nowMarker = useMemo(() => {
    if (!timelineRange || !timelineLayout) return null;
    const end = timelineRange.end;
    const start = timelineRange.start;
    const ratio = daysBetween(start, end) / timelineLayout.totalDays;
    const x =
      timelineLayout.padding +
      ratio * (timelineLayout.viewWidth - timelineLayout.padding * 2);
    const bandStartDate = new Date(end);
    bandStartDate.setDate(bandStartDate.getDate() - 29);
    const bandStartRatio =
      daysBetween(start, bandStartDate) / timelineLayout.totalDays;
    const bandStartX =
      timelineLayout.padding +
      Math.max(0, bandStartRatio) * (timelineLayout.viewWidth - timelineLayout.padding * 2);
    return { x, bandStartX };
  }, [timelineRange, timelineLayout]);

  const periodLabel = useMemo(() => {
    const found = PERIOD_OPTIONS.find((option) => option.value === period);
    return found ? found.label : '선택 기간';
  }, [period]);

  useEffect(() => {
    const analysisOptions = companyOptions.filter((option) => option !== '전체');
    if (viewMode === 'company' && analysisOptions.length > 0) {
      if (!analysisCompany || !analysisOptions.includes(analysisCompany)) {
        setAnalysisCompany(analysisOptions[0]);
      }
    }
  }, [viewMode, analysisCompany, companyOptions]);

  useEffect(() => {
    if (viewMode === 'company') {
      setAnalysisFiltersOpen(false);
    }
  }, [viewMode]);

  useEffect(() => {
    setSelectedEvent(null);
  }, [analysisCompany, period]);

  useEffect(() => {
    if (selectedEvent && !analysisPointsInRange.find((event) => event.id === selectedEvent.id)) {
      setSelectedEvent(null);
    }
  }, [analysisPointsInRange, selectedEvent]);

  const displayCount = useMemo(() => {
    if (viewMode === 'company') {
      return analysisCompany ? analysisPointsInRange.length : 0;
    }
    return timelineEvents.length;
  }, [viewMode, analysisCompany, analysisPointsInRange.length, timelineEvents.length]);

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <section className="securities-market">
      <div className="market-header">
        <div>
          <h2 className="section-title">🏦 국내 증권사 AI 동향</h2>
          <div className="market-subtitle">
            최근 업데이트 {lastUpdated ? formatDate(lastUpdated) : '-'} · {periodLabel} {displayCount}건
          </div>
        </div>
        <div className="view-toggle">
          <button
            type="button"
            className={`toggle-button ${viewMode === 'timeline' ? 'active' : ''}`}
            onClick={() => setViewMode('timeline')}
          >
            전체 타임라인
          </button>
          <button
            type="button"
            className={`toggle-button ${viewMode === 'company' ? 'active' : ''}`}
            onClick={() => setViewMode('company')}
          >
            회사 분석
          </button>
        </div>
      </div>

      {viewMode === 'timeline' && (
        <div className="filters">
          <div className="filter-group">
            <label htmlFor="market-search">검색</label>
            <input
              id="market-search"
              type="text"
              value={search}
              placeholder="회사/키워드 검색"
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="filter-group">
            <label htmlFor="market-company">회사</label>
            <select
              id="market-company"
              value={timelineCompany}
              onChange={(event) => setTimelineCompany(event.target.value)}
            >
              {companyOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="market-type">유형</label>
            <select
              id="market-type"
              value={type}
              onChange={(event) => setType(event.target.value)}
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="market-area">영역</label>
            <select
              id="market-area"
              value={area}
              onChange={(event) => setArea(event.target.value)}
            >
              {AREA_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="market-period">기간</label>
            <select
              id="market-period"
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
            >
              {PERIOD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {viewMode === 'timeline' && timelineEvents.length === 0 ? (
        <div className="market-empty">
          <div className="empty-title">조건에 맞는 업데이트가 없어요</div>
          <div className="empty-desc">필터를 줄이거나 기간을 넓혀보세요.</div>
        </div>
      ) : viewMode === 'timeline' ? (
        <div className="event-list">
          {timelineEvents.map((event) => (
            <article
              key={event.id}
              className={`event-card ${event.sources?.[0]?.url ? 'is-clickable has-link' : ''}`}
              role={event.sources?.[0]?.url ? 'button' : undefined}
              tabIndex={event.sources?.[0]?.url ? 0 : undefined}
              onClick={() => openSource(event.sources?.[0]?.url)}
              onKeyDown={(cardEvent) => handleCardKeyDown(cardEvent, event.sources?.[0]?.url)}
            >
              {event.sources?.[0]?.url && (
                <span className="event-link-icon" aria-hidden>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 3h7v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M10 14L21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M21 21H3V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              )}
              <div className="event-meta">
                <span className="event-date">{formatDate(event.date)}</span>
                <span className="event-company">{event.company}</span>
                <span className="event-type">{mapTypeGroup(event.type)}</span>
              </div>
              <h3 className="event-title">{event.title}</h3>
              <p className="event-summary">{event.oneLiner}</p>
              <div className="event-tags">
                {mapAreaGroups(event.areas || []).map((item) => (
                  <span key={item} className="event-tag">
                    {item}
                  </span>
                ))}
                {(event.tags || []).map((tag) => (
                  <span key={tag} className="event-tag secondary">
                    #{tag}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="company-analysis">
          {!analysisCompany ? (
            <div className="market-empty">
              <div className="empty-title">회사를 선택해 주세요</div>
              <div className="empty-desc">회사 분석 모드에서는 특정 증권사를 기준으로 봅니다.</div>
            </div>
          ) : (
            (() => {
              const analysisOptions = companyOptions.filter((option) => option !== '전체');

              return (
                <>
                  <div className="analysis-header">
                    <div>
                      <h3>{analysisCompany} 이벤트 추이</h3>
                      <p>주간 업데이트 건수 기준</p>
                    </div>
                    <div className="analysis-controls">
                      <select
                        className="analysis-select"
                        value={analysisCompany}
                        onChange={(event) => setAnalysisCompany(event.target.value)}
                      >
                        {analysisOptions.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                      <select
                        className="analysis-select"
                        value={period}
                        onChange={(event) => setPeriod(event.target.value)}
                      >
                        {PERIOD_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="analysis-filter-toggle"
                        onClick={() => setAnalysisFiltersOpen((prev) => !prev)}
                      >
                        {analysisFiltersOpen ? '필터 닫기' : '필터 열기'}
                      </button>
                      <div className="analysis-count">{analysisEvents.length}건</div>
                    </div>
                  </div>

                  {analysisFiltersOpen && (
                    <div className="analysis-filters">
                      <div className="analysis-filter-group">
                        <label htmlFor="analysis-search">검색</label>
                        <input
                          id="analysis-search"
                          type="text"
                          value={search}
                          placeholder="키워드 검색"
                          onChange={(event) => setSearch(event.target.value)}
                        />
                      </div>
                      <div className="analysis-filter-group">
                        <label htmlFor="analysis-type">유형</label>
                        <select
                          id="analysis-type"
                          value={type}
                          onChange={(event) => setType(event.target.value)}
                        >
                          {TYPE_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="analysis-filter-group">
                        <label htmlFor="analysis-area">영역</label>
                        <select
                          id="analysis-area"
                          value={area}
                          onChange={(event) => setArea(event.target.value)}
                        >
                          {AREA_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}

                  <div className="analysis-kpis">
                    <div className="analysis-kpi">
                      <div className="analysis-kpi-label">최근 이벤트</div>
                      <div className="analysis-kpi-value">
                        {analysisKpis.lastDate ? formatDate(analysisKpis.lastDate) : '-'}
                      </div>
                    </div>
                    <div className="analysis-kpi">
                      <div className="analysis-kpi-label">경과일</div>
                      <div className="analysis-kpi-value">
                        {analysisKpis.daysSinceLast === null ? '-' : `D+${analysisKpis.daysSinceLast}`}
                      </div>
                    </div>
                    <div className="analysis-kpi">
                      <div className="analysis-kpi-label">총 이벤트</div>
                      <div className="analysis-kpi-value">{analysisKpis.total}건</div>
                    </div>
                    <div className="analysis-kpi">
                      <div className="analysis-kpi-label">중앙 간격</div>
                      <div className="analysis-kpi-value">{analysisKpis.medianGap}일</div>
                    </div>
                    <div className="analysis-kpi">
                      <div className="analysis-kpi-label">최장 공백</div>
                      <div className="analysis-kpi-value">{analysisKpis.maxGap}일</div>
                    </div>
                  </div>

                  <div className="analysis-timeline">
                    <div className="timeline-header">
                      <div>
                        <h4>이벤트 타임라인</h4>
                        <p>점 클릭 시 상세가 표시됩니다.</p>
                      </div>
                      <div className="timeline-legend">
                        {TYPE_OPTIONS.filter((item) => item !== '전체').map((label) => {
                          const key = TYPE_KEYS[label];
                          const isActive = activeTypes[key];
                          return (
                            <button
                              key={label}
                              type="button"
                              className={`legend-item ${isActive ? 'active' : 'inactive'}`}
                              onClick={() =>
                                setActiveTypes((prev) => ({
                                  ...prev,
                                  [key]: !prev[key]
                                }))
                              }
                            >
                              <span
                                className="legend-dot"
                                style={{ backgroundColor: TYPE_COLORS[label] }}
                              />
                              <span className="legend-label">{label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                    {!timelineRange || analysisPointsInRange.length === 0 ? (
                      <div className="chart-empty">표시할 이벤트가 없습니다.</div>
                    ) : (
                      <div className="timeline-scroll">
                        <svg
                          className="timeline-svg"
                          width="100%"
                          height={timelineLayout.height}
                          viewBox={`0 0 ${timelineLayout.viewWidth} ${timelineLayout.height}`}
                          role="img"
                        >
                          <defs>
                            <radialGradient id="grad-product" cx="35%" cy="35%" r="70%">
                              <stop offset="0%" stopColor="#ffd1e1" />
                              <stop offset="100%" stopColor="#ff6b9d" />
                            </radialGradient>
                            <radialGradient id="grad-partner" cx="35%" cy="35%" r="70%">
                              <stop offset="0%" stopColor="#ffe3b3" />
                              <stop offset="100%" stopColor="#ffa500" />
                            </radialGradient>
                            <radialGradient id="grad-ops" cx="35%" cy="35%" r="70%">
                              <stop offset="0%" stopColor="#c9f2ee" />
                              <stop offset="100%" stopColor="#4ecdc4" />
                            </radialGradient>
                            <radialGradient id="grad-external" cx="35%" cy="35%" r="70%">
                              <stop offset="0%" stopColor="#d9d2ff" />
                              <stop offset="100%" stopColor="#6a5acd" />
                            </radialGradient>
                          </defs>

                          {nowMarker && (
                            <rect
                              x={nowMarker.bandStartX}
                              y={18}
                              width={nowMarker.x - nowMarker.bandStartX}
                              height={timelineLayout.height - 68}
                              className="timeline-band"
                            />
                          )}

                          <line
                            x1={timelineLayout.padding}
                            x2={timelineLayout.viewWidth - timelineLayout.padding}
                            y1={timelineLayout.height - 50}
                            y2={timelineLayout.height - 50}
                            className="timeline-axis"
                          />

                          {(() => {
                            const ticks = [];
                            const start = timelineRange.start;
                            const end = timelineRange.end;
                            if (period === 'all') {
                              let current = new Date(start.getFullYear(), start.getMonth(), 1);
                              while (current <= end) {
                                ticks.push(new Date(current));
                                current = addMonths(current, 1);
                              }
                            } else {
                              let current = new Date(start);
                              while (current <= end) {
                                ticks.push(new Date(current));
                                current.setDate(current.getDate() + 7);
                              }
                            }
                            return ticks.map((tick) => {
                              const ratio =
                                daysBetween(timelineRange.start, tick) / timelineLayout.totalDays;
                              const x =
                                timelineLayout.padding +
                                ratio * (timelineLayout.viewWidth - timelineLayout.padding * 2);
                              const shouldLabel =
                                period === 'all'
                                  ? tick.getMonth() % 2 === 0
                                  : true;
                              return (
                                <g key={tick.toISOString()}>
                                  <line
                                    x1={x}
                                    x2={x}
                                    y1={timelineLayout.height - 50}
                                    y2={18}
                                    className="timeline-grid"
                                  />
                                  <line
                                    x1={x}
                                    x2={x}
                                    y1={timelineLayout.height - 50}
                                    y2={timelineLayout.height - 44}
                                    className="timeline-tick"
                                  />
                                  {shouldLabel && (
                                    <text
                                      x={x}
                                      y={timelineLayout.height - 28}
                                      className="timeline-tick-label"
                                    >
                                      {period === 'all' ? formatMonth(tick) : formatShortDate(tick)}
                                    </text>
                                  )}
                                </g>
                              );
                            });
                          })()}

                          {selectedEvent && timelineRange && (
                            (() => {
                              const xRatio =
                                daysBetween(timelineRange.start, toDateOnly(selectedEvent.date)) /
                                timelineLayout.totalDays;
                              const x =
                                timelineLayout.padding +
                                xRatio * (timelineLayout.viewWidth - timelineLayout.padding * 2);
                              return (
                                <line
                                  x1={x}
                                  x2={x}
                                  y1={18}
                                  y2={timelineLayout.height - 50}
                                  className="timeline-selected-line"
                                />
                              );
                            })()
                          )}

                          {analysisPointsInRange.map((event) => {
                            const xRatio =
                              daysBetween(timelineRange.start, event.dateObj) / timelineLayout.totalDays;
                            const x =
                              timelineLayout.padding +
                              xRatio * (timelineLayout.viewWidth - timelineLayout.padding * 2);
                            const key = TYPE_KEYS[event.typeGroup] || 'product';
                            const isActive = activeTypes[key];
                            const gradientId = `grad-${key}`;
                            return (
                              <circle
                                key={event.id}
                                cx={x}
                                cy={timelineLayout.height - 70}
                                r={selectedEvent?.id === event.id ? 6 : 5}
                                fill={`url(#${gradientId})`}
                                className={`timeline-point ${isActive ? 'active' : 'inactive'} ${
                                  selectedEvent?.id === event.id ? 'selected' : ''
                                }`}
                                onClick={() => {
                                  if (isActive) {
                                    setSelectedEvent(event);
                                  }
                                }}
                              />
                            );
                          })}
                          {nowMarker && (
                            <line
                              x1={nowMarker.x}
                              x2={nowMarker.x}
                              y1={18}
                              y2={timelineLayout.height - 50}
                              className="timeline-now"
                            />
                          )}
                        </svg>
                      </div>
                    )}
                  </div>

                  <div className="analysis-distribution">
                    <div className="distribution-card type">
                      <h4>유형 분포</h4>
                      {Object.entries(typeDistribution).map(([label, count]) => {
                        const total = analysisKpis.total || 1;
                        const pct = Math.round((count / total) * 100);
                        return (
                          <div key={label} className="distribution-row">
                            <div className="distribution-label">{label}</div>
                            <div className="distribution-bar">
                              <div
                                className="distribution-fill"
                                style={{ width: `${pct}%`, background: TYPE_COLORS[label] || '#ff6b9d' }}
                              />
                            </div>
                            <div className="distribution-count">{count}건</div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="distribution-card area">
                      <h4>영역 분포</h4>
                      {Object.entries(areaDistribution).map(([label, count]) => {
                        const total = analysisKpis.total || 1;
                        const pct = Math.round((count / total) * 100);
                        return (
                          <div key={label} className="distribution-row">
                            <div className="distribution-label">{label}</div>
                            <div className="distribution-bar">
                              <div
                                className="distribution-fill secondary"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className="distribution-count">{count}건</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {selectedEvent && (
                    <div className="analysis-selected">
                      <div className="selected-header">
                        <div>
                          <div className="selected-title">{selectedEvent.title}</div>
                          <div className="selected-meta">
                            {formatDate(selectedEvent.date)} · {mapTypeGroup(selectedEvent.type)} ·{' '}
                            {mapAreaGroups(selectedEvent.areas || []).join(', ')}
                          </div>
                        </div>
                        {selectedEvent.sources?.[0]?.url && (
                          <button
                            type="button"
                            className="selected-link"
                            onClick={() => openSource(selectedEvent.sources[0].url)}
                          >
                            원문 보기
                          </button>
                        )}
                      </div>
                      <div className="selected-summary">{selectedEvent.oneLiner || '요약 정보가 없습니다.'}</div>
                    </div>
                  )}
                </>
              );
            })()
          )}
        </div>
      )}
    </section>
  );
}

export default SecuritiesAIMarket;
