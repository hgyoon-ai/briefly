import React, { useMemo, useState } from 'react';
import useDeveloperRadar from '../hooks/useDeveloperRadar';
import ModeHero from './ModeHero';
import '../styles/DeveloperRadar.css';

const SECTION_LABELS = {
  trending: '🔥 Trending',
  releases: '🚀 Releases',
  discussions: '💬 Discussions'
};

const SECTION_ORDER = ['trending', 'releases', 'discussions'];

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

function DeveloperRadarHome() {
  const { daily, loading, error } = useDeveloperRadar();
  const [selectedTag, setSelectedTag] = useState('전체');

  const clusters = useMemo(() => {
    if (!daily?.clusters) return [];
    return daily.clusters.slice().sort((a, b) => (b.score || 0) - (a.score || 0));
  }, [daily]);

  const tags = useMemo(() => {
    const raw = clusters.flatMap((cluster) => cluster.tags || []);
    const unique = Array.from(new Set(raw));
    return ['전체', ...unique];
  }, [clusters]);

  const filtered = useMemo(() => {
    if (selectedTag === '전체') return clusters;
    return clusters.filter((cluster) => (cluster.tags || []).includes(selectedTag));
  }, [clusters, selectedTag]);

  const grouped = useMemo(() => {
    return filtered.reduce((acc, cluster) => {
      const key = cluster.section || 'trending';
      if (!acc[key]) acc[key] = [];
      acc[key].push(cluster);
      return acc;
    }, {});
  }, [filtered]);

  if (loading) {
    return <div className="loading">데이터를 불러오는 중...</div>;
  }

  if (error || !daily) {
    return <div className="error">데이터를 불러올 수 없습니다.</div>;
  }

  return (
    <section className="developer-radar">
      <ModeHero
        icon="🧭"
        title="개발 레이더"
        summary="개발자 커뮤니티 신기술을 포착합니다."
        help={[
          '카드 하나는 하나의 엔티티(프로젝트/툴) 클러스터입니다.',
          '근거 배지는 소스별 상승 지표를 요약해 보여줍니다.',
          '태그로 분야별로 빠르게 필터링할 수 있습니다.'
        ]}
        metaLabel="최근 업데이트"
        metaValue={formatDate(daily.date)}
        modeKey="developer"
      />

      <div className="radar-filters">
        <div className="radar-filter-label">태그</div>
        <div className="radar-tag-row">
          {tags.map((tag) => (
            <button
              key={tag}
              type="button"
              className={`radar-tag ${selectedTag === tag ? 'active' : ''}`}
              onClick={() => setSelectedTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="radar-sections">
        {SECTION_ORDER.map((sectionKey) => {
          const items = grouped[sectionKey] || [];
          if (items.length === 0) return null;
          return (
            <div key={sectionKey} className="radar-section">
              <div className="radar-section-header">
                <h3>{SECTION_LABELS[sectionKey] || 'Trending'}</h3>
                <span className="radar-section-count">{items.length}개</span>
              </div>
              <div className="radar-card-grid">
                {items.map((cluster) => (
                  <article key={cluster.id} className="radar-card">
                    <div className="radar-card-header">
                      <h4 className="radar-card-title">{cluster.name}</h4>
                      {cluster.status && (
                        <span className={`radar-chip ${cluster.status.toLowerCase()}`}>
                          {cluster.status}
                        </span>
                      )}
                    </div>
                    <p className="radar-card-oneliner">{cluster.oneLiner}</p>
                    <div className="radar-card-why">{cluster.whyNow}</div>
                    {cluster.evidence?.length ? (
                      <div className="radar-evidence">
                        {cluster.evidence.map((item, index) => (
                          <span key={`${cluster.id}-ev-${index}`} className="radar-evidence-chip">
                            <span className="radar-evidence-source">{item.source}</span>
                            <span className="radar-evidence-metric">{item.metric}</span>
                            <span className="radar-evidence-value">{item.value}</span>
                          </span>
                        ))}
                      </div>
                    ) : null}
                    {cluster.links?.length ? (
                      <div className="radar-links">
                        {cluster.links.map((link, index) => (
                          <a
                            key={`${cluster.id}-link-${index}`}
                            href={link.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {link.label}
                          </a>
                        ))}
                      </div>
                    ) : null}
                    {cluster.tags?.length ? (
                      <div className="radar-tags">
                        {cluster.tags.map((tag) => (
                          <span key={`${cluster.id}-tag-${tag}`} className="radar-tag-chip">
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default DeveloperRadarHome;
