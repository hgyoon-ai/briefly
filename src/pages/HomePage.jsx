import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';
import IndustryHome from '../components/IndustryHome';
import SecuritiesAIMarket from '../components/SecuritiesAIMarket';
import { ADMIN_ICON } from '../constants/ui';

const STORAGE_KEY = 'briefly.homeTabs';
const DEFAULT_STATE = {
  mode: 'market',
  briefingTab: 'ai',
  marketTab: 'securities'
};

const loadHomeState = () => {
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

function HomePage() {
  const [homeState, setHomeState] = useState(loadHomeState);
  const { mode, briefingTab, marketTab } = homeState;

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(homeState));
  }, [homeState]);

  const activeTab = useMemo(
    () => (mode === 'market' ? marketTab : briefingTab),
    [mode, marketTab, briefingTab]
  );

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

      <div className="home-container">
        <nav className="home-nav-shell">
          <div className="home-mode-row">
          <div className="home-mode-label">모드</div>
          <div className="home-mode-switch">
            <button
              className={`tab-button mode-button ${mode === 'market' ? 'active' : ''}`}
              title="마켓"
              aria-label="마켓"
              onClick={() => {
                setHomeState((prev) => ({ ...prev, mode: 'market' }));
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
                setHomeState((prev) => ({ ...prev, mode: 'briefing' }));
              }}
            >
              <span className="mode-icon" aria-hidden>
                📌
              </span>
              <span className="mode-text">브리핑</span>
            </button>
          </div>
          <div className="home-mode-status">{mode === 'market' ? '마켓' : '브리핑'}</div>
        </div>
          <div className="home-nav-divider" />
          <div className="home-tabs-row">
            {mode === 'market' ? (
            <button
              className={`tab-button ${activeTab === 'securities' ? 'active' : ''}`}
              onClick={() => {
                setHomeState((prev) => ({ ...prev, marketTab: 'securities' }));
              }}
            >
              🏦 증권AI
            </button>
            ) : (
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
            )}
          </div>
        </nav>

        <main className="main-content">
          {mode === 'market' ? (
            <SecuritiesAIMarket />
          ) : (
            <IndustryHome tab={activeTab} />
          )}
        </main>
      </div>
    </div>
  );
}

export default HomePage;
