import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';
import IndustryHome from '../components/IndustryHome';
import SecuritiesAIMarket from '../components/SecuritiesAIMarket';
import DeveloperRadarHome from '../components/DeveloperRadarHome';
import { ADMIN_ICON } from '../constants/ui';

const STORAGE_KEY = 'briefly.homeTabs';
const DEFAULT_STATE = {
  mode: 'securities',
  briefingTab: 'ai',
  marketTab: 'securities-ai'
};

const loadHomeState = () => {
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
        parsed.briefingTab === 'finance' ||
        parsed.briefingTab === 'semiconductor' ||
        parsed.briefingTab === 'ev'
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

function HomePage() {
  const [homeState, setHomeState] = useState(loadHomeState);
  const { mode, briefingTab, marketTab } = homeState;

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(homeState));
  }, [homeState]);

  const activeTab = useMemo(() => {
    if (mode === 'securities') return marketTab;
    if (mode === 'industry') return briefingTab;
    return 'developer';
  }, [mode, marketTab, briefingTab]);

  return (
    <div className="home-page">
      <header className="header">
        <div className="header-content">
          <span className="admin-spacer" aria-hidden />
          <h1>Briefly</h1>
          <Link to="/admin" className="admin-link" title="관리자 페이지">
            <span>{ADMIN_ICON}</span>
          </Link>
        </div>
      </header>

      <div className="home-container">
        <nav className="home-nav-shell">
          <div className="home-mode-row">
          <div className="home-mode-label">모드</div>
          <div className="home-mode-switch">
            <button
              className={`tab-button mode-button ${mode === 'securities' ? 'active' : ''}`}
              title="증권사"
              aria-label="증권사"
              onClick={() => {
                setHomeState((prev) => ({ ...prev, mode: 'securities' }));
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
                setHomeState((prev) => ({ ...prev, mode: 'industry' }));
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
                setHomeState((prev) => ({ ...prev, mode: 'developer' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                🧭
              </span>
              <span className="mode-text">개발</span>
            </button>
          </div>
          <div className="home-mode-status">
            {mode === 'securities' ? '증권사' : mode === 'industry' ? '산업' : '개발'}
          </div>
        </div>
          <div className="home-nav-divider" />
          <div className="home-tabs-row">
            {mode === 'securities' ? (
              <>
                <button
                  className={`tab-button ${activeTab === 'securities-ai' ? 'active' : ''}`}
                  onClick={() => {
                    setHomeState((prev) => ({ ...prev, marketTab: 'securities-ai' }));
                  }}
                >
                  🏦 증권AI
                </button>
                <button
                  className={`tab-button ${activeTab === 'securities-updates' ? 'active' : ''}`}
                  onClick={() => {
                    setHomeState((prev) => ({ ...prev, marketTab: 'securities-updates' }));
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
                    setHomeState((prev) => ({ ...prev, briefingTab: 'ai' }));
                  }}
                >
                  🤖 AI
                </button>
                <button
                  className={`tab-button ${activeTab === 'finance' ? 'active' : ''}`}
                  onClick={() => {
                    setHomeState((prev) => ({ ...prev, briefingTab: 'finance' }));
                  }}
                >
                  💼 금융/규제
                </button>
                <button
                  className={`tab-button ${activeTab === 'semiconductor' ? 'active' : ''}`}
                  onClick={() => {
                    setHomeState((prev) => ({ ...prev, briefingTab: 'semiconductor' }));
                  }}
                >
                  🔌 반도체
                </button>
                <button
                  className={`tab-button ${activeTab === 'ev' ? 'active' : ''}`}
                  onClick={() => {
                    setHomeState((prev) => ({ ...prev, briefingTab: 'ev' }));
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

        <main className={`main-content mode-${mode}`}>
          {mode === 'securities' ? (
            <SecuritiesAIMarket
              dataset={activeTab}
              title={
                activeTab === 'securities-updates'
                  ? '국내 증권사 업데이트'
                  : '국내 증권사 AI 동향'
              }
            />
          ) : mode === 'industry' ? (
            <IndustryHome tab={activeTab} />
          ) : (
            <DeveloperRadarHome />
          )}
        </main>
      </div>
    </div>
  );
}

export default HomePage;
