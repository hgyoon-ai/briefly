import React, { useEffect, useMemo, useState } from 'react';
import '../styles/ModeHero.css';

const buildExpandedKey = (modeKey) => `briefly.modeHelpExpanded.${modeKey || 'default'}`;
const buildSeenKey = (modeKey) => `briefly.modeHelpSeen.${modeKey || 'default'}`;

function ModeHero({
  icon,
  title,
  summary,
  help = [],
  metaLabel,
  metaValue,
  actions = null,
  modeKey = 'default'
}) {
  const expandedKey = useMemo(() => buildExpandedKey(modeKey), [modeKey]);
  const seenKey = useMemo(() => buildSeenKey(modeKey), [modeKey]);
  const hasHelp = Array.isArray(help) ? help.length > 0 : Boolean(help);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    try {
      if (!hasHelp) {
        setExpanded(false);
        return;
      }
      const stored = localStorage.getItem(expandedKey);
      const seen = localStorage.getItem(seenKey);
      if (stored !== null) {
        setExpanded(stored === 'true');
        return;
      }
      if (seen === null) {
        setExpanded(true);
        setTimeout(() => {
          try {
            localStorage.setItem(seenKey, 'true');
          } catch (error) {
            // ignore
          }
        }, 0);
      } else {
        setExpanded(false);
      }
    } catch (error) {
      setExpanded(hasHelp);
    }
  }, [expandedKey, seenKey, hasHelp]);

  const toggleExpanded = () => {
    if (!hasHelp) return;
    setExpanded((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(expandedKey, String(next));
      } catch (error) {
        // ignore
      }
      return next;
    });
  };

  return (
    <div className="mode-hero">
      <div className="mode-hero-row">
        <div className="mode-hero-top">
          <div className="mode-hero-title">
            {icon ? <span className="mode-hero-icon">{icon}</span> : null}
            <span className="mode-hero-title-text">{title}</span>
          </div>
          <div className="mode-hero-right">
            {metaLabel ? (
              <div className="mode-hero-meta">
                <div className="mode-hero-meta-label">{metaLabel}</div>
                <div className="mode-hero-meta-value">{metaValue || '-'}</div>
              </div>
            ) : null}
            {actions ? <div className="mode-hero-actions-slot">{actions}</div> : null}
          </div>
        </div>
        <div className="mode-hero-bottom">
          {summary ? <div className="mode-hero-summary-text">{summary}</div> : null}
          {hasHelp ? (
            <button type="button" className="mode-hero-toggle" onClick={toggleExpanded}>
              {expanded ? '닫기' : '자세히'}
            </button>
          ) : null}
        </div>
      </div>
      {hasHelp && expanded ? (
        <ul className="mode-hero-help">
          {(Array.isArray(help) ? help : [help]).map((item, index) => (
            <li key={`${modeKey}-help-${index}`}>{item}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export default ModeHero;
