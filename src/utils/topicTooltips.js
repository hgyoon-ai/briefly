export const TOPIC_TOOLTIPS = {
  Models: '신규 모델/업데이트/성능 변화',
  Training: '학습 방법/파인튜닝/학습 레시피',
  Inference: '추론 최적화/서빙/성능·비용 개선',
  Tooling: '에이전트/SDK/개발 툴/워크플로',
  Infra: 'GPU/가속기/클라우드 인프라',
  Safety: '안전성/정렬/보안/규제',
  Research: '논문/벤치마크/기초 연구',
  Product: '제품/기능 출시/서비스 업데이트',
  Business: '투자/파트너십/인수합병',
  Data: '데이터셋/라이선스/데이터 거버넌스',
};

export const getTopicTooltip = (topic) => TOPIC_TOOLTIPS[topic] || '';
