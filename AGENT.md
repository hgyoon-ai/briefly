# Agent 운영 문서

이 문서는 에이전트가 세션이 끊겨도 Briefly 프로젝트의 목적, 범위, 규칙, 현재 상태를 빠르게 이해하도록 돕는다.

## 1. 프로젝트 한 줄 요약
Briefly는 AI/반도체/EV 등 산업 트렌드를 일간·주간·월간 이슈로 요약해 제공하는 서비스다.

## 2. 현재 범위
- 테마: AI, 반도체, EV (추후 확장 가능)
- 주기: 일간/주간/월간 요약
- 제외: 신뢰도 낮은 출처, 중복 기사, 광고성 콘텐츠

## 3. 파이프라인 개요
1) 수집: 지정된 소스에서 최신 기사/이슈 수집
2) 정제: 중복 제거, 신뢰도 필터링
3) 분류: 테마/주기 기준으로 그룹화
4) 요약: 핵심 포인트 3줄 요약 + 주요 이슈 리스트
5) 노출: 홈 페이지 섹션별 렌더링
6) 주간/월간 집계: `archive`에 저장된 daily 데이터 기반 롤링 집계

## 3-1. 크롤링 실행
- 파이프라인 스크립트: `scripts/run_pipeline.py`
- 롤업 전용 스크립트: `scripts/build_rollups_from_archive.py`
- 테스트용 아카이브 생성: `scripts/generate_test_archives.py`
- Python 의존성: `requirements.txt`
- LLM 요약: OpenAI (환경 변수 `OPENAI_API_KEY` 필요)
- GitHub API: `MY_GITHUB_TOKEN` 사용 가능 (rate limit 완화)
- 환경 변수 로딩: `.env` (python-dotenv)

## 3-2. 크롤링 소스 (최소 셋업)
- OpenAI Blog, Anthropic Blog, Google DeepMind Blog, Meta AI Blog
- Microsoft Research Blog, NVIDIA Developer Blog, Hugging Face Blog, PyTorch Blog
- GitHub Releases (동적 검색)
- Hugging Face Hub Trending

## 3-3. 수집 제한 및 윈도우
- 소스별 수집 제한: RSS 15 / GitHub 40 / HF 30 (총 150)
- 롤링 윈도우: daily 24h / weekly 7d / monthly 30d
- 타임존: KST 기준
 - Weekly/Monthly: daily 아카이브 기반 + 중요도(importanceScore) 가중치 반영

## 4. 수집 규칙
- 소스 우선순위: 공식 리포트 > 주요 매체 > 블로그/커뮤니티
- 중복 기준: 제목/요약 유사도, 동일 사건의 변형 기사 병합
- 시간 범위: 일간(24h), 주간(7d), 월간(30d)

## 5. 분류/요약 규칙
- 일간: 중요도(importanceScore) 기반 주요 이슈 2~5개 노출
- 주간: daily 아카이브 기반 롤업 + LLM 재요약 주요 이슈
- 월간: daily 아카이브 기반 롤업 + LLM 재요약 주요 이슈
- 모든 요약은 사실 중심, 과장/추측 금지

## 6. 데이터 저장 구조
- 운영 데이터: `public/latest/` (웹에서 사용하는 최신 JSON)
- 아카이브: `archive/YYYY/MM/YYYY-MM-DD_{period}.json`
- 크롤링 직후 `archive`에 저장하고, 최신 데이터는 `public/latest`에 반영
- daily 카드 필드: `status`, `hash`, `importanceScore` 포함

## 7. 출력 포맷 (초안)
```
{
  "period": "daily|weekly|monthly",
  "theme": "AI|Semiconductor|EV",
  "summary": ["...", "...", "..."],
  "issues": [
    {"title": "...", "source": "...", "url": "...", "date": "YYYY-MM-DD"}
  ],
  "stats": {"collected": 0, "deduped": 0, "topics": 0}
}
```

## 8. 품질 기준
- 최소 커버리지: 각 테마당 주요 이슈 3건 이상
- 신뢰도: 공식/주요 매체 비중 70% 이상 권장
- 재현성: 동일 입력 시 동일한 요약 구조 유지

## 9. 운영 체크리스트
- Daily: 수집 성공 여부, 누락된 테마 확인
- Weekly: 중복 규칙 점검, 트렌드 급변 테마 검토
- Monthly: 소스 품질 점검, 테마 확장 필요성 평가

## 10. 현재 상태
- UI: 일/주/월 섹션 구조 구현 (React/Vite)
- 데이터: `public/latest` JSON 사용 중, 아카이브는 `archive`에 저장
- 크롤링/요약 파이프라인: Python 스크립트 추가 완료
- weekly/monthly 이슈: 모달에서 관련 기사 링크(최대 3개) 표시

## 11. 다음 액션
- Gemini API 키 설정 후 파이프라인 실행
- GitHub Actions 스케줄러 추가

## 12. 결정 로그
- 2026-01-22: 에이전트 세션 복구를 위해 AGENT.md 도입
