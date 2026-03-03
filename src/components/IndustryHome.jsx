import React, { useEffect, useState } from 'react';
import TodaysSummary from './TodaysSummary';
import ModeHero from './ModeHero';
import WeeklyTrends from './WeeklyTrends';
import MonthlyTrends from './MonthlyTrends';
import useMockData from '../hooks/useMockData';

const formatDate = (value) => {
  if (!value) return '-';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

function IndustryHome({ tab }) {
  const { today, weekly, monthly, loading, error } = useMockData(tab);
  const [activePeriodTab, setActivePeriodTab] = useState('weekly');
  const [selectedWeeklyTopic, setSelectedWeeklyTopic] = useState(null);
  const [selectedMonthlyTopic, setSelectedMonthlyTopic] = useState(null);

  useEffect(() => {
    setActivePeriodTab('weekly');
    setSelectedWeeklyTopic(null);
    setSelectedMonthlyTopic(null);
  }, [tab]);

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (error || !today || !weekly || !monthly) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  const activeRange = activePeriodTab === 'weekly'
    ? `${weekly.range.from} ~ ${weekly.range.to}`
    : `${monthly.range.from} ~ ${monthly.range.to}`;

  return (
    <>
      <ModeHero
        icon="🏭"
        title="산업 브리핑"
        summary="산업별 주요 업데이트를 일간·주간·월간으로 요약합니다."
        help={[
          '오늘의 요약은 핵심 3줄과 오늘의 소식 카드로 구성됩니다.',
          '주간/월간은 토픽을 눌러 추세와 관련 소식을 확인합니다.',
          '소식 카드를 클릭하면 관련 기사 모달이 열립니다.'
        ]}
        metaLabel="최근 업데이트"
        metaValue={formatDate(today.date)}
        modeKey="industry"
      />
      <TodaysSummary data={today} tab={tab} showTitle={false} compact />

      <div className="period-tabs-section">
        <div className="period-tabs">
          <button
            className={`period-tab ${activePeriodTab === 'weekly' ? 'active' : ''}`}
            onClick={() => {
              setActivePeriodTab('weekly');
              setSelectedWeeklyTopic(null);
            }}
          >
            주간
          </button>
          <button
            className={`period-tab ${activePeriodTab === 'monthly' ? 'active' : ''}`}
            onClick={() => {
              setActivePeriodTab('monthly');
              setSelectedMonthlyTopic(null);
            }}
          >
            월간
          </button>
        </div>
        <div className="period-range-note">조회 기간: {activeRange}</div>

        {activePeriodTab === 'weekly' && (
          <WeeklyTrends
            data={weekly}
            selectedTopic={selectedWeeklyTopic}
            onTopicSelect={setSelectedWeeklyTopic}
          />
        )}

        {activePeriodTab === 'monthly' && (
          <MonthlyTrends
            data={monthly}
            selectedTopic={selectedMonthlyTopic}
            onTopicSelect={setSelectedMonthlyTopic}
          />
        )}
      </div>
    </>
  );
}

export default IndustryHome;
