import React, { useState, useEffect } from 'react';
import '../styles/HomePage.css';
import TodaysSummary from '../components/TodaysSummary';
import WeeklyTrends from '../components/WeeklyTrends';
import MonthlyTrends from '../components/MonthlyTrends';

function HomePage() {
  const [todayData, setTodayData] = useState(null);
  const [weeklyData, setWeeklyData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('AI');
  const [activePeriodTab, setActivePeriodTab] = useState('weekly');
  const [selectedWeeklyTopic, setSelectedWeeklyTopic] = useState(null);
  const [selectedMonthlyTopic, setSelectedMonthlyTopic] = useState(null);

  useEffect(() => {
    // mock 데이터 로드
    Promise.all([
      fetch('/mock/dummy_today.json').then(res => res.json()),
      fetch('/mock/dummy_7d.json').then(res => res.json()),
      fetch('/mock/dummy_30d.json').then(res => res.json())
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

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (!todayData || !weeklyData || !monthlyData) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="home-page">
      <header className="header">
        <h1>Briefly</h1>
        <p className="date-range">
          {monthlyData.range.from} ~ {monthlyData.range.to}
        </p>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'AI' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('AI');
            setSelectedWeeklyTopic(null);
            setSelectedMonthlyTopic(null);
          }}
        >
          🤖 AI
        </button>
        <button
          className="tab-button disabled"
          disabled
        >
          🔌 반도체 <span className="coming-soon">(예정)</span>
        </button>
        <button
          className="tab-button disabled"
          disabled
        >
          ⚡ 전기차 <span className="coming-soon">(예정)</span>
        </button>
      </nav>

      <main className="main-content">
        {/* 오늘 내용 요약 */}
        <TodaysSummary data={todayData} />

        {/* 주간/월간 탭 */}
        <div className="period-tabs-section">
          <div className="period-tabs">
            <button
              className={`period-tab ${activePeriodTab === 'weekly' ? 'active' : ''}`}
              onClick={() => {
                setActivePeriodTab('weekly');
                setSelectedWeeklyTopic(null);
              }}
            >
              주간 ({weeklyData.range.from} ~ {weeklyData.range.to})
            </button>
            <button
              className={`period-tab ${activePeriodTab === 'monthly' ? 'active' : ''}`}
              onClick={() => {
                setActivePeriodTab('monthly');
                setSelectedMonthlyTopic(null);
              }}
            >
              월간 ({monthlyData.range.from} ~ {monthlyData.range.to})
            </button>
          </div>

          {/* 주간 트렌드 */}
          {activePeriodTab === 'weekly' && (
            <WeeklyTrends 
              data={weeklyData} 
              selectedTopic={selectedWeeklyTopic}
              onTopicSelect={setSelectedWeeklyTopic}
            />
          )}

          {/* 월간 트렌드 */}
          {activePeriodTab === 'monthly' && (
            <MonthlyTrends 
              data={monthlyData} 
              selectedTopic={selectedMonthlyTopic}
              onTopicSelect={setSelectedMonthlyTopic}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default HomePage;
