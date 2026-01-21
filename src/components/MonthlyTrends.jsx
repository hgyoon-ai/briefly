import React, { useState } from 'react';
import TopIssues from './TopIssues';
import '../styles/MonthlyTrends.css';

function MonthlyTrends({ data, selectedTopic, onTopicSelect }) {
  const { topTopics, topicTrend, topIssues, kpis, weeklyData } = data;
  const [hoveredSegment, setHoveredSegment] = useState(null);

  // 날짜별로 트렌드 데이터 정렬
  const trendByDate = topicTrend.reduce((acc, item) => {
    if (!acc[item.date]) {
      acc[item.date] = [];
    }
    acc[item.date].push(item);
    return acc;
  }, {});

  // 선택된 토픽의 데이터만 필터링
  const filteredTrend = selectedTopic
    ? topicTrend.filter(item => item.topic === selectedTopic)
    : topicTrend;

  // 최대값 계산
  const maxCount = Math.max(...filteredTrend.map(item => item.count), 1);

  // 날짜 객체 배열로 변환 후 정렬
  const sortedDates = Object.keys(trendByDate).sort();

  return (
    <section className="monthly-trends">
      {/* 주간별 토픽 분석 - 가로 누적 막대 그래프 */}
      {weeklyData && weeklyData.length > 0 && (
        <div className="weekly-analysis-section">
          <h3>주간별 토픽 분석 - 점유율 추이</h3>
          <div className="weekly-chart-html">
            {(() => {
              // 데이터 변환
              const allTopics = new Set();
              weeklyData.forEach(week => {
                Object.keys(week.topicCounts).forEach(topic => allTopics.add(topic));
              });
              let topicArray = Array.from(allTopics).slice(0, 5);
              const colors = ['#ff6b9d', '#ffa500', '#4ecdc4', '#95e1d3', '#f38181', '#c0c0c0'];

              return (
                <div className="weekly-bars-container">
                  {weeklyData.map((week, idx) => {
                    const totalCount = Object.values(week.topicCounts).reduce((a, b) => a + b, 0);
                    
                    // 날짜 범위 추출
                    const weekString = week.week;
                    const dateMatch = weekString.match(/\((.*?)\)/);
                    const dateRange = dateMatch ? dateMatch[1] : '';
                    
                    // 상위 5개 토픽 계산
                    const topicCounts = { ...week.topicCounts };
                    const topicPercentages = {};
                    
                    topicArray.forEach(topic => {
                      topicPercentages[topic] = totalCount > 0 ? parseFloat(((topicCounts[topic] || 0) / totalCount * 100).toFixed(1)) : 0;
                      delete topicCounts[topic];
                    });
                    
                    // Other 계산
                    const remainingCounts = Object.values(topicCounts).reduce((a, b) => a + b, 0);
                    topicPercentages['Other'] = totalCount > 0 ? parseFloat(((remainingCounts) / totalCount * 100).toFixed(1)) : 0;

                    return (
                      <div key={idx} className="weekly-bar-item">
                        <div className="weekly-label">
                          <div className="week-name">W{idx + 1}</div>
                          <div className="week-date">{dateRange}</div>
                        </div>
                        <div className="bar-row">
                          {[...topicArray, 'Other'].map((topic, tidx) => {
                            const percentage = topicPercentages[topic];
                            const segmentId = `${idx}-${topic}`;
                            const isHovered = hoveredSegment === segmentId;
                            
                            return (
                              <div
                                key={topic}
                                className={`bar-segment ${isHovered ? 'active' : ''}`}
                                style={{
                                  width: `${percentage}%`,
                                  backgroundColor: colors[tidx],
                                  opacity: percentage > 0 ? 1 : 0.3,
                                  minWidth: percentage > 3 ? 'auto' : '0'
                                }}
                                title={`${topic} (${percentage}%)`}
                                onMouseEnter={() => setHoveredSegment(segmentId)}
                                onMouseLeave={() => setHoveredSegment(null)}
                                onTouchStart={(e) => {
                                  e.preventDefault();
                                  setHoveredSegment(isHovered ? null : segmentId);
                                }}
                                onTouchEnd={(e) => {
                                  e.preventDefault();
                                }}
                              >
                                {(percentage > 5 || isHovered) && (
                                  <span className="segment-label">{percentage}%</span>
                                )}
                                {isHovered && (
                                  <div className="segment-tooltip">
                                    {topic}<br/>{percentage}%
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}

                  {/* 범례 */}
                  <div className="chart-legend">
                    {[...topicArray, 'Other'].map((topic, idx) => (
                      <div key={topic} className="legend-item">
                        <div
                          className="legend-color"
                          style={{ backgroundColor: colors[idx] }}
                        />
                        <span>{topic}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Top Issues */}
      <TopIssues issues={topIssues} />

      {/* 선택된 토픽의 점유율 비교 */}
      {selectedTopic && (
        <div className="topic-comparison-section">
          <div className="trend-header">
            <h3>📊 {selectedTopic} - 월간 점유율</h3>
            <button 
              className="close-button"
              onClick={() => onTopicSelect(null)}
            >
              ✕
            </button>
          </div>
          <div className="topic-comparison">
            <div className="comparison-item">
              <div className="comparison-label">{selectedTopic} 점유율</div>
              <div className="comparison-bar">
                <div
                  className="comparison-fill"
                  style={{
                    width: `${kpis.marketShare[selectedTopic] || 0}%`,
                    backgroundColor: '#ff6b9d'
                  }}
                >
                  <span className="comparison-percent">{kpis.marketShare[selectedTopic] || 0}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default MonthlyTrends;
