#!/usr/bin/env python3
"""
박재현 선생님 채널의 미응답 댓글 중 가장 최신 20개를 수집.

환경 변수:
    YOUTUBE_API_KEY: YouTube Data API v3 키
    CHANNEL_ID: 수집할 채널 ID (기본: UCFhliquzU-5I83gMrb-HIVw)
    MAX_COMMENTS: 최대 수집 개수 (기본: 20)

출력:
    data/fresh.json - 수집한 미응답 댓글 리스트
"""
import os, json, sys, time, datetime
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("의존성 누락: pip install google-api-python-client", file=sys.stderr)
    sys.exit(1)

API_KEY = os.environ.get('YOUTUBE_API_KEY')
CHANNEL_ID = os.environ.get('CHANNEL_ID', 'UCFhliquzU-5I83gMrb-HIVw')
MAX_COMMENTS = int(os.environ.get('MAX_COMMENTS', '20'))
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / 'fresh.json'

if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY 환경변수가 설정되지 않음", file=sys.stderr)
    sys.exit(1)


def fetch_unanswered(limit=20):
    """미응답(totalReplyCount==0) 댓글 중 가장 최신 limit개 반환"""
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    collected = []
    seen = set()
    token = None

    for page in range(30):  # 최대 30 페이지 (3,000개 스캔) 안전장치
        try:
            resp = youtube.commentThreads().list(
                part='snippet',
                allThreadsRelatedToChannelId=CHANNEL_ID,
                maxResults=100,
                pageToken=token,
                textFormat='plainText',
                order='time',
            ).execute()
        except HttpError as e:
            print(f"API 오류: {e}", file=sys.stderr)
            break

        items = resp.get('items', [])
        if not items:
            break

        for item in items:
            top = item['snippet']['topLevelComment']
            sn = top['snippet']
            cid = top['id']
            if cid in seen:
                continue
            seen.add(cid)

            # 미응답인 것만
            if item['snippet'].get('totalReplyCount', 0) > 0:
                continue

            collected.append({
                'commentId': cid,
                'author': sn.get('authorDisplayName', ''),
                'text': sn.get('textDisplay', '').replace('\r\n', ' ').replace('\n', ' '),
                'date': sn['publishedAt'][:10],
                'publishedAt': sn['publishedAt'],
                'likes': sn.get('likeCount', 0),
                'video': sn.get('videoId', ''),
                'authorChannelUrl': sn.get('authorChannelUrl', ''),
            })

            if len(collected) >= limit:
                return collected

        token = resp.get('nextPageToken')
        if not token:
            break
        time.sleep(0.1)

    return collected


def main():
    print(f"[fetch] 미응답 댓글 최대 {MAX_COMMENTS}개 수집 시작...", file=sys.stderr)
    comments = fetch_unanswered(MAX_COMMENTS)
    comments.sort(key=lambda c: c['publishedAt'], reverse=True)

    OUT_FILE.write_text(
        json.dumps(comments, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"[fetch] {len(comments)}개 수집 완료 → {OUT_FILE}", file=sys.stderr)

    # GitHub Actions에서 사용할 수 있게 표준출력으로 요약
    print(json.dumps({
        'count': len(comments),
        'top_author': comments[0]['author'] if comments else None,
        'top_date': comments[0]['publishedAt'] if comments else None,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
