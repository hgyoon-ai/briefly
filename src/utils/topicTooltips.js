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
  Earnings: '실적/가이던스/수익성',
  Demand: '수요·공급/출하량/재고',
  Manufacturing: '생산·공정/수율/공장',
  Policy: '정책/규제/보조금',
  Investment: '투자/CapEx/증설',
  Competition: '경쟁/시장점유율',
  Roadmap: '기술·제품 로드맵',

  // Finance/regulation tab
  Regulation: '규제/입법/가이드라인/감독 정책',
  Enforcement: '제재/과징금/과태료/행정처분/사고 대응',
  Privacy: '개인정보/데이터 보호/유출',
  Security: '보안/피싱/취약점/인증/침해사고',
  Fintech: '핀테크/오픈금융/마이데이터/신규 서비스',
  Payments: '결제/송금/간편결제/정산',
  Crypto: '가상자산/스테이블코인/디지털자산 제도',
  Compliance: 'AML/FDS/이상거래/내부통제',
  MarketInfra: '거래·결제 인프라(STO/거래소/예탁 등)',
};

export const getTopicTooltip = (topic) => TOPIC_TOOLTIPS[topic] || '';
