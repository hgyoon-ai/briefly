# briefly
Briefly는 AI를 활용해 AI·반도체·EV 등 산업 트렌드를 간결하게 요약해 제공하는 서비스입니다.

## 📁 폴더 구조

```
briefly/
├── src/
│   ├── pages/              # 페이지 컴포넌트
│   │   └── HomePage.jsx
│   ├── components/         # UI 컴포넌트
│   │   ├── TodaysSummary.jsx
│   │   ├── WeeklyTrends.jsx
│   │   └── MonthlyTrends.jsx
│   ├── styles/             # 스타일시트
│   │   ├── index.css
│   │   ├── HomePage.css
│   │   ├── TodaysSummary.css
│   │   ├── WeeklyTrends.css
│   │   └── MonthlyTrends.css
│   └── main.jsx
├── mock/                   # API 개발 전 더미 데이터 저장
│   ├── dummy_today.json    # 오늘의 요약 데이터
│   ├── dummy_7d.json       # 주간 트렌드 데이터
│   └── dummy_30d.json      # 월간 트렌드 데이터
├── index.html
├── package.json
└── vite.config.js
```

## 🚀 실행 방법

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```
자동으로 브라우저가 열리고 `http://localhost:5173`에서 확인할 수 있습니다.

### 3. 프로덕션 빌드
```bash
npm run build
```

### 4. 빌드 결과 미리보기
```bash
npm run preview
```

## 📱 페이지 구성

### 홈페이지 (HomePage)

**오늘의 요약 섹션:**
- 📊 수집/중복제거/주제 개수 카드
- 📝 핵심 내용 (3줄 요약)
- 📰 주요 뉴스 카드 (하이퍼링크 포함)

**주간 트렌드 섹션:**
- 🏆 주간 Top 토픽 목록 (클릭 시 일별 트렌드 표시)
- ⚠️ 주요 이슈 목록
- 📊 선택한 토픽의 일별 트렌드 차트

**월간 트렌드 섹션:**
- 📈 월간 통계 (수집/중복제거/이슈)
- 🔥 떠오르는 주제들 (상위 3개)
- 🏆 월간 Top 토픽 목록 (클릭 시 월별 추세 표시)
- ⚠️ 주요 이슈 목록
- 📊 선택한 토픽의 월별 추세 차트

## 💻 기술 스택

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: CSS3 (Mobile-First Responsive Design)

## ✨ 특징

✅ 모바일 우선 반응형 디자인
✅ 가벼운 성능 (Vite 번들)
✅ 더미 데이터로 즉시 테스트 가능
