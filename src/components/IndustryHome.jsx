import React, { useEffect, useState } from 'react';
import TodaysSummary from './TodaysSummary';
import WeeklyTrends from './WeeklyTrends';
import MonthlyTrends from './MonthlyTrends';
import useMockData from '../hooks/useMockData';

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

  return (
    <>
      <TodaysSummary data={today} tab={tab} />

      <div className="period-tabs-section">
        <div className="period-tabs">
          <button
            className={`period-tab ${activePeriodTab === 'weekly' ? 'active' : ''}`}
            onClick={() => {
              setActivePeriodTab('weekly');
              setSelectedWeeklyTopic(null);
            }}
          >
            주간 ({weekly.range.from} ~ {weekly.range.to})
          </button>
          <button
            className={`period-tab ${activePeriodTab === 'monthly' ? 'active' : ''}`}
            onClick={() => {
              setActivePeriodTab('monthly');
              setSelectedMonthlyTopic(null);
            }}
          >
            월간 ({monthly.range.from} ~ {monthly.range.to})
          </button>
        </div>

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
