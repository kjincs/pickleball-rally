#!/usr/bin/env python3
"""Review collection, source checks, and publishing for Codex-prepared editions. No AI API key."""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TYPES = ['official','reporting','brand','forum','social']
CATEGORIES = ['Style', 'Community', 'News', 'Trends', 'Paddle knowledge']
DIRECTIONS = ['More like this', 'Keep the mix', 'Less like this', 'Already seen / repetitive', 'Check the facts or source']


def load(path):
    return json.loads((ROOT / path).read_text())


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)


def request_json(url, token=None, attempts=3):
    headers = {'Accept': 'application/json', 'User-Agent': 'RallyEditorial/1.0'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    for attempt in range(attempts):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=180) as response:
                return json.load(response)
        except HTTPError as error:
            # Do not print request bodies, auth headers, or provider error bodies.
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise RuntimeError(f'API returned HTTP {error.code}; previous edition preserved') from None
        except (URLError, TimeoutError):
            if attempt == attempts - 1:
                raise RuntimeError('API connection failed; previous edition preserved') from None
        time.sleep(2 ** attempt)


def canonical_url(value):
    if not isinstance(value, str):
        raise ValueError('Source URL must be a string')
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('Source URL must be an HTTPS link')
    query = [(k,v) for k,v in parse_qsl(u.query) if not k.startswith('utm_') and k not in ('fbclid','gclid')]
    return urlunsplit(('https',u.netloc.lower(),u.path.rstrip('/') or '/',urlencode(query),''))


def fields(body):
    result = {}
    for match in re.finditer(r'^### (.+)\n+([\s\S]*?)(?=^### |\Z)', body, re.M):
        result[match.group(1).strip()] = match.group(2).strip()
    return result


def parse_reviews(issues, trusted, editions):
    """Only valid form submissions, known story IDs, and latest reviewer edits count."""
    latest = {}
    trusted = {name.lower() for name in trusted} if trusted is not None else None
    for issue in issues:
        if 'pull_request' in issue or not issue.get('title','').startswith('[Review]'):
            continue
        author = issue.get('user',{}).get('login','').lower()
        if not author or (trusted is not None and author not in trusted):
            continue
        f = fields(issue.get('body') or '')
        eid, sid = f.get('Edition ID'), f.get('Story ID')
        if eid not in editions:
            continue
        story = next((s for s in editions[eid]['stories'] if s['id'] == sid), None)
        if sid != 'edition' and story is None:
            continue
        score = re.match(r'^([1-5])(?:\s|$)', f.get('Score',''))
        direction = f.get('What should we change?','')
        comment = f.get('Your thoughts','')
        if comment == '_No response_':
            comment = ''
        if not score and direction not in DIRECTIONS and not comment:
            continue
        review = {'reviewer':author,'edition':eid,'story':sid,'title':story['title'] if story else 'Whole edition',
                  'category':story['category'] if story else 'Edition','score':int(score.group(1)) if score else None,
                  'direction':direction if direction in DIRECTIONS else None,'comment':comment[:2000], 'updated_at':issue.get('updated_at',''),
                  'number':issue['number']}
        key = (author,eid,sid)
        if key not in latest or (review['updated_at'],review['number']) > (latest[key]['updated_at'],latest[key]['number']):
            latest[key] = review
    return sorted(latest.values(), key=lambda r:(r['updated_at'],r['number']))


def fetch_reviews(config, editions):
    repo = config['repository']
    token = os.environ.get('GITHUB_TOKEN')
    issues = []
    # Include closed and edited reviews. Paginate until the history is exhausted.
    page = 1
    while True:
        batch = request_json(f'https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}', token=token)
        if not isinstance(batch,list):
            raise ValueError('Unexpected GitHub issues response')
        issues.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    trusted = None if config.get('review_mode') == 'open' else [repo.split('/')[0], *config['trusted_reviewers']]
    # A rolling window prevents very old preferences from overpowering current feedback.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=42)).isoformat().replace('+00:00','Z')
    return [r for r in parse_reviews(issues,trusted,editions) if r['updated_at'] >= cutoff]


def checked_stories(candidates, cited, previous, today, max_age):
    accepted, seen = [], set(previous)
    for candidate in candidates:
        try:
            s = dict(candidate)
            url = canonical_url(s['url'])
            if url not in cited or url in seen or s['category'] not in CATEGORIES:
                continue
            if s['kind'] not in ('news','evergreen'):
                continue
            published = date.fromisoformat(s['published_at']) if s.get('published_at') else None
            if published and published > today:
                continue
            if s['kind'] == 'news' and (not published or (today-published).days > max_age):
                continue
            if s.get('source_language') not in ('en','zh') or s.get('source_type') not in SOURCE_TYPES:
                continue
            if s['source_type'] in ('forum','social') and urlsplit(url).path in ('','/'):
                continue
            for key,limit in [('title_zh',110),('summary_zh',500),('why_zh',220),('title',110),('summary',500),('why',220),('source',100)]:
                if not isinstance(s.get(key),str) or not s[key].strip() or len(s[key]) > limit:
                    raise ValueError('Invalid story field')
            s['url'] = url
            s['id'] = hashlib.sha256(url.encode()).hexdigest()[:12]
            seen.add(url)
            accepted.append(s)
        except (ValueError,KeyError,TypeError):
            continue
    return accepted


def context_snapshot(config):
    index = load('data/index.json')
    editions = {eid: load(f'data/editions/{eid}.json') for eid in index['editions']}
    reviews = fetch_reviews(config, editions)
    now = datetime.now(timezone.utc)
    return {'collected_at': now.isoformat(), 'today': str(now.astimezone(ZoneInfo(config['timezone'])).date()),
            'config': config, 'preferences': load('data/preferences.json'), 'reviews': reviews,
            'previous_stories': [{'title':s['title'],'url':s['url']} for e in editions.values() for s in e['stories']]}


def publish_draft(draft, config):
    """Publish research prepared in Codex. No AI API call or key is used."""
    index = load('data/index.json')
    previous = {canonical_url(s['url']) for eid in index['editions'] for s in load(f'data/editions/{eid}.json')['stories']}
    now = datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo(config['timezone'])).date()
    if draft.get('date') != str(today):
        raise ValueError('Draft date must match today in the publication timezone')
    evidence = draft.get('sources', [])
    if not evidence or any(not s.get('checked_at') or not s.get('notes') for s in evidence):
        raise ValueError('Research evidence needs source links, checked_at dates, and notes')
    cited = {canonical_url(s['url']) for s in evidence}
    stories = checked_stories(draft.get('stories',[]),cited,previous,today,config['max_news_age_days'])
    if not stories or len(stories) != len(draft.get('stories',[])):
        raise ValueError('Every draft story must pass source/date/duplicate checks; nothing published')
    if len(stories) > config['edition_size']:
        raise ValueError('Draft exceeds configured edition size')
    if sum(s['source_type'] in ('forum','social') for s in stories) > config.get('max_community_stories',2):
        raise ValueError('Too many community perspectives')
    for key in ('feedback_note','feedback_note_zh'):
        if not isinstance(draft.get(key),str) or not draft[key].strip() or len(draft[key]) > 500:
            raise ValueError('Bilingual feedback notes are required')
    guidance = draft.get('guidance',[])
    if not isinstance(guidance,list) or len(guidance)>5 or any(not isinstance(x,str) or len(x)>220 for x in guidance):
        raise ValueError('Guidance must be at most five concise preferences')
    count = draft.get('review_count')
    if not isinstance(count,int) or isinstance(count,bool) or count < 0:
        raise ValueError('Valid review count required')
    eid = str(today) + '-' + now.strftime('%H%M%S') + '-' + hashlib.sha256(json.dumps(stories,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:6]
    edition = {'id':eid,'date':str(today),'created_at':now.isoformat(),'seed':False,'research_method':'codex',
               'feedback_note':draft['feedback_note'],'feedback_note_zh':draft['feedback_note_zh'],
               'review_count':count,'stories':stories,'sources':evidence}
    # Validate the entire draft before modifying the edition index.
    write(f'data/editions/{eid}.json',edition)
    write('data/preferences.json',{'updated_at':now.isoformat(),'guidance':guidance,'review_count':count})
    write('data/index.json',{'editions':[eid,*index['editions']]})
    print(f'Prepared {eid}: {len(stories)} stories using {count} reviews. No API key used.')


def validate_site():
    config = load('config.json')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',config['repository']):
        raise ValueError('Set repository to owner/repo in config.json')
    ZoneInfo(config['timezone'])
    if not 1 <= config['edition_size'] <= 8:
        raise ValueError('Edition size must be 1–8')
    index = load('data/index.json')
    if not index['editions'] or len(set(index['editions'])) != len(index['editions']):
        raise ValueError('Invalid edition index')
    for eid in index['editions']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',eid):
            raise ValueError('Invalid edition ID')
        e = load(f'data/editions/{eid}.json')
        if e['id'] != eid or not e['stories']:
            raise ValueError('Invalid edition')
        date.fromisoformat(e['date'])
        ids = set()
        for s in e['stories']:
            canonical_url(s['url'])
            if s['category'] not in CATEGORIES or s['id'] in ids:
                raise ValueError('Invalid story category or duplicate ID')
            ids.add(s['id'])
            if s.get('source_type') not in SOURCE_TYPES or s.get('source_language') not in ('en','zh'):
                raise ValueError('Invalid source context')
            for field in ('title','summary','why','source','title_zh','summary_zh','why_zh'):
                if not isinstance(s.get(field),str) or not s[field].strip():
                    raise ValueError('Story field missing')
    print(f'Validated {len(index["editions"])} editions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--context', metavar='OUTPUT', help='Fetch public GitHub reviews and save context for Codex')
    parser.add_argument('--publish', metavar='DRAFT', help='Validate and publish a source-checked bilingual draft')
    args = parser.parse_args()
    try:
        config = load('config.json')
        if args.context:
            Path(args.context).write_text(json.dumps(context_snapshot(config),ensure_ascii=False,indent=2)+'\n')
            print('Review context saved to '+args.context)
        elif args.publish:
            publish_draft(json.loads(Path(args.publish).read_text()), config)
            validate_site()
        else:
            validate_site()
    except Exception as error:
        print(f'Edition not published: {error}',file=sys.stderr)
        sys.exit(1)
