# 박재현 채널 댓글 답글 시스템

YouTube 댓글에 AI 초안을 자동 작성해주는 대시보드입니다. 진료실 윈도우든 맥북이든 브라우저로 URL만 열면 됩니다.

## 사용 흐름

1. 브라우저에서 `https://[GitHub아이디].github.io/[리포이름]` 열기
2. "🔄 수집 (20개)" 버튼 클릭
3. 1~2분 기다림 (GitHub Actions가 댓글 가져오고 AI 초안 작성)
4. 새 댓글 20개가 답글 초안과 함께 표시됨
5. 각 댓글의 "📋 복사 + YouTube Studio 열기" 클릭 → YouTube Studio에서 붙여넣기 → 전송

## 한 번만 하는 셋업

### 1. Anthropic API 키 발급

1. https://console.anthropic.com/ 접속 → 계정 생성 (이미 있으면 로그인)
2. Settings → Billing → 결제 수단 등록 (월 1~3달러 예상)
3. Settings → API Keys → "Create Key" → 키 복사 (sk-ant-... 로 시작)

### 2. YouTube Data API 키 발급

이미 있으시면 건너뛰세요. 없으면:

1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 → "API 및 서비스" → "라이브러리" → "YouTube Data API v3" 검색 → 사용 설정
3. "사용자 인증 정보" → "API 키 만들기" → 키 복사

### 3. GitHub 리포 생성 + 코드 push

```bash
# 이 폴더에서:
cd github_repo
git init -b main
git add .
git commit -m "Initial commit"

# GitHub에서 새 리포 만들고 (private 권장), 그 URL을 origin으로 추가
git remote add origin https://github.com/[YOUR_USERNAME]/[REPO_NAME].git
git push -u origin main
```

### 4. Secrets 등록

GitHub 리포 페이지에서 Settings → Secrets and variables → Actions → "New repository secret" 로 다음 3개 추가:

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | YouTube API 키 (AIza...) |
| `ANTHROPIC_API_KEY` | Anthropic API 키 (sk-ant-...) |
| `CHANNEL_ID` | `UCFhliquzU-5I83gMrb-HIVw` (선생님 채널 ID) |

### 5. GitHub Pages 활성화

리포 Settings → Pages → "Build and deployment" → Source: "Deploy from a branch" → Branch: `main` → Folder: `/docs` → Save

약 1분 뒤 `https://[YOUR_USERNAME].github.io/[REPO_NAME]/` 에서 대시보드를 볼 수 있게 됩니다.

### 6. Personal Access Token (PAT) 발급 - "수집" 버튼용

대시보드의 "수집" 버튼이 GitHub Actions를 직접 호출하기 위해 필요합니다.

1. https://github.com/settings/personal-access-tokens/new 접속
2. Token name: `youtube-comments-dashboard`
3. Expiration: 1년 (또는 원하는 기간)
4. Repository access: "Only select repositories" → 방금 만든 리포 선택
5. Permissions → Repository permissions:
   - **Actions**: Read and write
   - **Contents**: Read
6. "Generate token" → 토큰 복사 (`github_pat_...` 형식)

### 7. 대시보드 첫 사용

1. 브라우저에서 `https://[USERNAME].github.io/[REPO_NAME]/` 열기
2. 자동으로 설정 다이얼로그 뜸
3. 리포지토리: `[USERNAME]/[REPO_NAME]` 입력
4. PAT: 6번에서 복사한 토큰 붙여넣기
5. "저장" 클릭
6. "🔄 수집 (20개)" 클릭 → 1~2분 후 새 댓글 20개 표시됨

## 비용

- **GitHub** (Pages + Actions): 무료 (월 2,000분 한도, 우리는 월 ~30분 사용)
- **YouTube Data API**: 무료 (일일 10,000 unit 한도, 우리는 ~10 unit/일)
- **Anthropic API** (Claude Haiku 4.5): 댓글 20개 처리당 약 $0.02. 매일 1번 수집해도 월 $0.60. 보통 월 1~2달러

## 파일 구조

```
github_repo/
├── scripts/
│   ├── fetch.py       # YouTube API로 미응답 댓글 20개 수집
│   ├── draft.py       # Anthropic API로 답글 초안 작성
│   └── build.py       # docs/data.json 생성
├── data/
│   ├── fresh.json     # 방금 수집한 원본
│   └── drafted.json   # 초안 포함
├── docs/              # GitHub Pages 호스팅 폴더
│   ├── index.html     # 대시보드 페이지
│   └── data.json      # 대시보드가 읽는 데이터
├── .github/workflows/
│   └── collect.yml    # "수집" 버튼이 트리거하는 워크플로우
└── requirements.txt
```

## 트러블슈팅

**"수집" 클릭했는데 안 됨**
- 설정에서 리포지토리 이름이 정확한지 확인 (`owner/repo` 형식)
- PAT 권한이 Actions: Read and write 인지 확인
- 브라우저 콘솔(F12)에 GitHub API 오류 메시지 있는지 확인

**1~2분 지나도 갱신 안 됨**
- GitHub 리포의 "Actions" 탭에서 실행 결과 확인
- 실패했다면 로그에서 어느 단계 오류인지 확인 (YOUTUBE_API_KEY 만료, ANTHROPIC_API_KEY 한도 초과 등)

**"data.json을 불러올 수 없습니다"**
- Pages 빌드가 아직 안 끝났을 수 있음. 1~2분 기다린 후 새로고침
- 리포 Settings → Pages에서 배포 상태 확인

**AI 초안 톤이 마음에 안 듦**
- `scripts/draft.py` 안의 `SYSTEM_PROMPT` 수정 후 push
- 다음 수집부터 새 톤으로 반영됨

## 변경 / 확장

- **수집 주기 자동화** 원하면 `.github/workflows/collect.yml`에 `schedule: - cron: '0 11 * * 0'` (일요일 8pm KST) 추가
- **한 번에 가져오는 수 변경** 원하면 대시보드 "수집" 버튼이 호출하는 inputs.max_comments 값 수정 (HTML의 `max_comments: '20'` 부분)
