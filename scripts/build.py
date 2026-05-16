#!/usr/bin/env python3
"""
drafted.json → docs/data.json 으로 복사.
대시보드(docs/index.html)는 docs/data.json을 fetch해서 렌더링합니다.
"""
import json, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_IN = ROOT / 'data' / 'drafted.json'
DATA_OUT = ROOT / 'docs' / 'data.json'

if not DATA_IN.exists():
    raise SystemExit(f"입력 파일 없음: {DATA_IN}")

comments = json.loads(DATA_IN.read_text(encoding='utf-8'))

# publishedAt 내림차순 (최신순) - YouTube Studio 매칭
comments.sort(key=lambda c: c.get('publishedAt',''), reverse=True)

payload = {
    'comments': comments,
    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'updated_kst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST'),
}

DATA_OUT.parent.mkdir(exist_ok=True)
DATA_OUT.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding='utf-8'
)
print(f"[build] {DATA_OUT} 작성 완료 ({len(comments)}개 댓글)")
