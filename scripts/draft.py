#!/usr/bin/env python3
"""
fetch.py가 만든 data/fresh.json의 각 댓글에 대해
Anthropic Claude API로 박재현 선생님 톤의 답글 초안을 작성.

환경 변수:
    ANTHROPIC_API_KEY: Anthropic API 키
    DRAFT_MODEL: 사용할 모델 (기본: claude-haiku-4-5)

출력:
    data/drafted.json - 답글 초안 포함된 최종 댓글 리스트
"""
import os, json, sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("의존성 누락: pip install anthropic", file=sys.stderr)
    sys.exit(1)

API_KEY = os.environ.get('ANTHROPIC_API_KEY')
MODEL = os.environ.get('DRAFT_MODEL', 'claude-haiku-4-5')
DATA_DIR = Path(__file__).parent.parent / 'data'
IN_FILE = DATA_DIR / 'fresh.json'
OUT_FILE = DATA_DIR / 'drafted.json'

if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY 환경변수가 설정되지 않음", file=sys.stderr)
    sys.exit(1)

if not IN_FILE.exists():
    print(f"ERROR: {IN_FILE} 없음. fetch.py를 먼저 실행하세요.", file=sys.stderr)
    sys.exit(1)


SYSTEM_PROMPT = """당신은 신경과 전문의 박재현 원장님의 YouTube 채널 댓글에 답글을 대신 작성하는 보조자입니다.

박재현 선생님 톤 가이드:
- 정중하고 따뜻한 한국어
- 2~4문장, 80~150자
- "~드립니다", "~바랍니다" 정중체
- 이모지 자제

의료법 안전 원칙 (필수):
1. 구체적 진단명·약물명을 단정해서 말하지 마세요
2. "정확한 진단은 진료실에서 받아보시기를 권합니다" 같은 안전 문구를 자연스럽게 포함하세요
3. 응급 증상(갑작스러운 시야 이상, 언어 장애, 한쪽 마비)이 의심되면 "즉시 응급실" 안내

댓글 유형별 응대:
- 짧은 감사 인사 → 짧고 따뜻하게 1-2문장
- 경험 공유 → 공감 + 격려
- 개별 상담 (긴 사연) → 공감 + 진료실 권유
- 단순 질문 → 일반적 답변 + 진료 권유

응답은 답글 본문만 출력하세요. 따옴표·머리말·해설 없이."""


def draft_one(client, comment):
    """단일 댓글에 답글 초안 작성"""
    user_msg = f"""원댓글 (작성자: {comment['author']}, 좋아요 {comment.get('likes',0)}):
\"\"\"
{comment['text'][:1000]}
\"\"\"

박재현 선생님이 직접 쓴 듯한 정중한 답글:"""
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text.strip()
        # 따옴표로 감싸여 있으면 제거
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        return text
    except Exception as e:
        print(f"  ! 드래프트 실패 ({comment['commentId']}): {e}", file=sys.stderr)
        return ""


def main():
    comments = json.loads(IN_FILE.read_text(encoding='utf-8'))
    print(f"[draft] {len(comments)}개 댓글에 초안 작성 시작 (모델: {MODEL})", file=sys.stderr)

    client = anthropic.Anthropic(api_key=API_KEY)

    drafted = []
    for i, c in enumerate(comments, 1):
        print(f"  [{i}/{len(comments)}] {c['author']}: {c['text'][:50]}...", file=sys.stderr)
        c['ai_draft'] = draft_one(client, c)
        drafted.append(c)

    OUT_FILE.write_text(
        json.dumps(drafted, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"[draft] 완료 → {OUT_FILE}", file=sys.stderr)
    print(json.dumps({
        'drafted_count': sum(1 for c in drafted if c.get('ai_draft')),
        'failed_count': sum(1 for c in drafted if not c.get('ai_draft')),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
