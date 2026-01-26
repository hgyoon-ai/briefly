import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';
import TodaysSummary from '../components/TodaysSummary';
import WeeklyTrends from '../components/WeeklyTrends';
import MonthlyTrends from '../components/MonthlyTrends';
import useMockData from '../hooks/useMockData';
import { ADMIN_ICON } from '../constants/ui';

function HomePage() {
  const [activeTab, setActiveTab] = useState('ai');
  const { today, weekly, monthly, loading, error } = useMockData(activeTab);
  const [activePeriodTab, setActivePeriodTab] = useState('weekly');
  const [selectedWeeklyTopic, setSelectedWeeklyTopic] = useState(null);
  const [selectedMonthlyTopic, setSelectedMonthlyTopic] = useState(null);

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (error || !today || !weekly || !monthly) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <div className="home-page">
      <header className="header">
        <div className="header-content">
          <h1>Briefly</h1>
          <Link to="/admin" className="admin-link" title="관리자 페이지">
            <span>{ADMIN_ICON}</span>
          </Link>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('ai');
            setSelectedWeeklyTopic(null);
            setSelectedMonthlyTopic(null);
            setActivePeriodTab('weekly');
          }}
        >
          🤖 AI
        </button>
        <button
          className={`tab-button ${activeTab === 'semiconductor' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('semiconductor');
            setSelectedWeeklyTopic(null);
            setSelectedMonthlyTopic(null);
            setActivePeriodTab('weekly');
          }}
        >
          🔌 반도체
        </button>
        <button
          className={`tab-button ${activeTab === 'ev' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('ev');
            setSelectedWeeklyTopic(null);
            setSelectedMonthlyTopic(null);
            setActivePeriodTab('weekly');
          }}
        >
          ⚡ 전기차
        </button>
      </nav>

      <main className="main-content">
        {/* 오늘 내용 요약 */}
        <TodaysSummary data={today} tab={activeTab} />

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

          {/* 주간 트렌드 */}
          {activePeriodTab === 'weekly' && (
            <WeeklyTrends 
              data={weekly} 
              selectedTopic={selectedWeeklyTopic}
              onTopicSelect={setSelectedWeeklyTopic}
            />
          )}

          {/* 월간 트렌드 */}
          {activePeriodTab === 'monthly' && (
            <MonthlyTrends 
              data={monthly} 
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
