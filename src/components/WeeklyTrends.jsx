import React, { useRef, useEffect, useState } from 'react';
import IssueModal from './IssueModal';
import TopIssues from './TopIssues';
import { getTopicTooltip } from '../utils/topicTooltips';
import '../styles/WeeklyTrends.css';

function WeeklyTrends({ data, selectedTopic, onTopicSelect }) {
  const { kpis, topTopics, topicTrend, topIssues, risingTopics } = data;
  const chartSectionRef = useRef(null);
  const hasInitialized = useRef(false);
  const [isUserInitiated, setIsUserInitiated] = useState(false);
  const [activeIssue, setActiveIssue] = useState(null);

  // 날짜별로 트렌드 데이터 정렬 (dayOfWeek 포함)
  const trendByDate = topicTrend.reduce((acc, item) => {
    if (!acc[item.date]) {
      acc[item.date] = {
        date: item.date,
        dayOfWeek: item.dayOfWeek,
        topics: []
      };
    }
    acc[item.date].topics.push(item);
    return acc;
  }, {});

  // 선택된 토픽의 데이터만 필터링
  const filteredTrend = selectedTopic
    ? topicTrend.filter(item => item.topic === selectedTopic)
    : topicTrend;

  // 최대값 계산
  const maxCount = Math.max(...filteredTrend.map(item => item.count), 1);

  // 첫 번째 주제를 기본으로 선택 (스크롤 없음)
  useEffect(() => {
    if (!hasInitialized.current && !selectedTopic && topTopics && topTopics.length > 0) {
      onTopicSelect(topTopics[0].name);
      hasInitialized.current = true;
    }
  }, [selectedTopic, topTopics, onTopicSelect]);

  // 토픽 선택 시 차트로 스크롤 (사용자 클릭 시에만)
  useEffect(() => {
    if (isUserInitiated && selectedTopic && chartSectionRef.current) {
      setTimeout(() => {
        chartSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [selectedTopic, isUserInitiated]);

  return (
    <section className="weekly-trends">
      {/* 주간 소식 */}
      <TopIssues title="주간 소식" issues={topIssues} onIssueSelect={setActiveIssue} />
      <IssueModal issue={activeIssue} onClose={() => setActiveIssue(null)} />

      {/* Top 토픽과 일별 차트 함께 */}
      <div className="topics-and-chart-container">
        {/* Top 토픽 목록 - 클릭 가능 */}
        <div className="all-topics-section">
          <h3 className="section-title-small">주간 Top 토픽</h3>
          <div className="topics-grid">
            {topTopics.map((topic, idx) => (
              <button
                key={idx}
                className={`topic-badge ${selectedTopic === topic.name ? 'active' : ''}`}
                title={(() => {
                  const tooltip = getTopicTooltip(topic.name);
                  return tooltip ? `${topic.name}: ${tooltip}` : topic.name;
                })()}
                onClick={() => {
                  setIsUserInitiated(true);
                  onTopicSelect(selectedTopic === topic.name ? null : topic.name);
                }}
              >
                <span className="topic-rank">#{idx + 1}</span>
                <span className="topic-label">{topic.name}</span>
                <span className="topic-count">{topic.count}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 선택된 토픽의 일별 트렌드 차트 */}
        {selectedTopic && (
          <div className="daily-trend-section inline" ref={chartSectionRef}>
            <div className="trend-header">
              <h3>📈 {selectedTopic}</h3>
              <button 
                className="close-button"
                onClick={() => onTopicSelect(null)}
              >
                ✕
              </button>
            </div>
            <div className="trend-chart">
              {Object.entries(trendByDate).map(([date, dateData]) => {
                const item = dateData.topics.find(i => i.topic === selectedTopic);
                return (
                  <div key={date} className="trend-day">
                    <div className="trend-bar-container">
                      <div
                        className="trend-bar animated"
                        style={{
                          height: item ? `${(item.count / maxCount) * 120}px` : '5px',
                          backgroundColor: '#ff6b9d'
                        }}
                        title={`${selectedTopic}: ${item?.count || 0}건`}
                      />
                    </div>
                    <div className="trend-count">{item?.count || 0}</div>
                    <div className="trend-date">{dateData.dayOfWeek}</div>
                    <div className="trend-date-full">{date}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default WeeklyTrends;
