#!/usr/bin/env python3
"""Index public Codrops GitHub demo metadata; do not crawl blocked Codrops pages.

python3 scripts/collect-codrops.py [--cache /path/to/github-pages.json] [--previews]
python3 scripts/collect-codrops.py --previews-only
The optional cache contains {'pages': [{'url': 'GitHub API URL', 'items': [...]}]}.

--previews resolves a preview image for every github.com/codrops repository through
the authenticated GitHub API (`gh api`), in this order: an image committed in the
repository (README-referenced or a conventional preview/screenshot/demo file),
pinned to the default-branch commit on raw.githubusercontent.com; a README image
hosted elsewhere (URL stored for hotlinking, never fetched here); GitHub's
generated social card. Image bytes are never downloaded, and tympanus.net is
never requested. --previews-only re-resolves previews for the existing catalog
without re-reading the repository list. Without either flag, previews already in
the catalog are carried over by item ID.
"""
import argparse
import base64
import concurrent.futures
import datetime
import hashlib
import html
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
TAG = 'https://tympanus.net/codrops/tag/webgl/'
API = 'https://api.github.com/users/codrops/repos?per_page=100&sort=updated'
TERMS = {
    'webgl': r'webgl', 'three.js': r'three[. -]?js', 'shaders': r'shader|glsl',
    'scroll': r'scroll', 'page-transition': r'transition', 'hover': r'hover',
    '3d': r'\b3d\b', 'particles': r'particle', 'gallery': r'gallery|grid',
    'slideshow': r'slideshow|slider', 'distortion': r'distort', 'cursor': r'cursor|mouse',
    'animation': r'animation|animated|effect|reveal',
}
# Titles and article URLs independently resolved through public search results on
# 2026-11-12 after the initial public tag listing was returned. No article body
# or inferred permalink is stored. This seed is preserved, not bulk-refreshed.
ARTICLES = [
 ('2026/10/21/atelier-ui-webgl-dom/', 'Atelier UI: Mixing WebGL and the DOM in a React UI Library', ['React Three Fiber','Next.js','scroll','page-transition']),
 ('2026/10/20/maria-vasilyeva-portfolio/', 'When a Website Becomes a Melody: Inside Maria Vasilyeva’s Portfolio', ['portfolio','sound','GLSL']),
 ('2026/10/17/image-compression-previewer/', 'Build a Browser-Based Image Compression Previewer with libvips-wasm', ['performance','wasm','Three.js']),
 ('2026/10/16/ksenia-kondrashova/', 'Just Trying to Do What I Like: Ksenia Kondrashova’s Path from Fun Demos to Paper Shaders', ['developer-spotlight','GLSL','Three.js']),
 ('2026/10/15/noho-redesign/', 'Knowing When to Do Less: Translating Noho’s Product DNA into Interaction', ['case-study','GSAP','performance']),
 ('2026/10/12/chasing-the-moment/', 'Chasing the Moment: Making a Short Film for the Browser with Three.js and GLSL', ['case-study','Three.js','GLSL']),
 ('2026/10/07/interlude-astro-page-transitions/', 'Interlude: A Starter for Custom Page Transitions in Astro', ['Astro','GSAP','page-transition']),
 ('2026/10/06/yichen-xie-portfolio/', 'Inside Yichen Xie’s Portfolio: Finding Joy in the Craft of Interaction', ['portfolio','GLSL','interaction']),
 ('2026/09/29/webflow-gsap-codetv-challenge/', 'The Drive: Building a Resident Evil Concept for the Webflow × GSAP × CodeTV Challenge', ['Webflow','GSAP','3D']),
 ('2026/09/28/wide-template/', 'Take It, Break It, Make It Yours: Inside Wide, an Open Source Grid Experiment by BL/S®', ['grid','GLSL','template']),
 ('2026/09/19/crumbled-paper-houdini-vat-threejs/', 'Building an Interactive Crumpled Paper Effect with Houdini VAT and Three.js', ['Three.js','physics','cannon-es']),
 ('2026/09/13/building-depth-designing-and-developing-a-3d-renderer-inside-figma/', 'Building Depth: Designing and Developing a 3D Renderer Inside Figma', ['Figma','3D','Three.js']),
 ('2026/09/05/building-an-infinite-loom-unravelling-images-into-threads-with-three-js/', 'Building an Infinite Loom: Unravelling Images into Threads with Three.js', ['marquee','Three.js']),
 ('2026/09/04/beyond-the-luminance-ramp-a-shape-aware-ascii-renderer-in-three-js/', 'Beyond the Luminance Ramp: A Shape-Aware ASCII Renderer in Three.js', ['ASCII','shaders','Three.js']),
 ('2026/09/03/from-rays-to-meshes-building-vercels-prism-with-vgpu/', 'From Rays to Meshes: Building Vercel’s Prism with vgpu', ['3D','GLSL','vgpu']),
 ('2026/09/02/breaking-the-frame-building-a-real-time-datamosh-effect-with-three-js/', 'Breaking the Frame: Building a Real-Time Datamosh Effect with Three.js', ['shaders','Three.js','post-processing']),
 ('2026/08/31/volatile-nexus-tinkering-with-glass-caustics-cubes-and-sound-in-three-js/', 'Volatile Nexus: Tinkering with Glass, Caustics, Cubes and Sound in Three.js', ['3D','particles','Three.js']),
 ('2026/08/25/building-a-mouse-following-square-lens-effect-with-three-js-and-glsl/', 'Building a Mouse-Following Square Lens Effect with Three.js and GLSL', ['cursor','distortion','Three.js']),
]


PREVIEW_FIELDS = ('preview', 'previewSource', 'previewHost', 'previewPath', 'commit', 'previewCollected',
                  # written by scripts/render-codrops-previews.mjs
                  'previewCommit', 'previewEntry', 'previewNote', 'previewSocialCard')
IMAGE_EXT = re.compile(r'\.(png|jpe?g|gif|webp|avif|svg)$', re.I)
CONVENTIONAL = re.compile(r'(?:^|/)(preview|screenshot|screenshots?|demo|cover|thumbnail|thumb)\.(png|jpe?g|gif|webp)$', re.I)
CONVENTIONAL_DIRS = ('', 'docs/', 'images/', 'img/')
# Status badges and CI shields are README images but not previews of the demo.
SKIP_HOSTS = ('img.shields.io', 'shields.io', 'badgen.net', 'travis-ci.org', 'travis-ci.com',
               'circleci.com', 'badge.fury.io', 'app.netlify.com', 'api.netlify.com', 'vercel.com', 'badg.es',
               # Generic placeholder generators used as demo content, not a picture of the demo.
               'generative-placeholders.glitch.me', 'placehold.co', 'placeholder.com', 'picsum.photos', 'placekitten.com')
BLOCKED_HOST = 'tympanus.net'
MARKDOWN_IMAGE = re.compile(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+["\'][^)]*["\'])?\s*\)')
HTML_IMAGE = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*["\']([^"\']+)["\']', re.I)
REFERENCE_IMAGE = re.compile(r'!\[([^\]]*)\]\[([^\]]*)\]')
REFERENCE_DEF = re.compile(r'^\s*\[([^\]]+)\]:\s*<?(\S+?)>?(?:\s+.*)?$', re.M)


class GhError(RuntimeError):
    def __init__(self, path, status, message):
        super().__init__(f'gh api {path}: {status} {message}')
        self.status = status


def gh(path, accept=None):
    """Call the GitHub REST API through the authenticated gh CLI (api.github.com only)."""
    cmd = ['gh', 'api', '--include', path]
    if accept:
        cmd += ['-H', 'Accept: ' + accept]
    for attempt in range(3):
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        head, _, body = result.stdout.partition('\r\n\r\n') if '\r\n\r\n' in result.stdout else result.stdout.partition('\n\n')
        status = int(re.match(r'HTTP/\S+\s+(\d+)', head).group(1)) if re.match(r'HTTP/\S+\s+(\d+)', head) else 0
        time.sleep(.25)
        if result.returncode == 0:
            return body if accept and 'sha' in accept else json.loads(body)
        if status in (403, 429) and 'rate limit' in (body + result.stderr).lower():
            raise GhError(path, status, 'rate limited; stopping before the catalog is replaced')
        if status in (404, 409, 451) or attempt == 2:
            raise GhError(path, status, (result.stderr or body).strip()[:200])
        time.sleep(2 * (attempt + 1))


def is_host(host, domain):
    return bool(host) and (host == domain or host.endswith('.' + domain))


def readme_images(text):
    """Image references from a README, in document order (markdown, reference-style and <img>)."""
    found = []
    for match in MARKDOWN_IMAGE.finditer(text):
        found.append((match.start(), match.group(1)))
    for match in HTML_IMAGE.finditer(text):
        found.append((match.start(), html.unescape(match.group(1))))
    defs = {key.lower(): url for key, url in REFERENCE_DEF.findall(text)}
    for match in REFERENCE_IMAGE.finditer(text):
        target = defs.get((match.group(2) or match.group(1)).lower())
        if target:
            found.append((match.start(), target))
    return [url.strip().strip('"\'') for _, url in sorted(found)]


def repo_path_for(ref, repo, readme_dir):
    """Map a README image reference to a path inside this repository, or None if remote."""
    parsed = urlparse(ref)
    host = (parsed.hostname or '').lower()
    if not parsed.scheme and not parsed.netloc:
        path = unquote(parsed.path)
        if not path:
            return None
        joined = urljoin('/' + readme_dir, path)
        return joined.lstrip('/')
    parts = [unquote(part) for part in parsed.path.split('/') if part]
    if host == 'raw.githubusercontent.com' and len(parts) > 3 and parts[0].lower() == 'codrops' and parts[1].lower() == repo.lower():
        return '/'.join(parts[3:])
    if host == 'github.com' and len(parts) > 4 and parts[0].lower() == 'codrops' and parts[1].lower() == repo.lower() and parts[2] in ('blob', 'raw'):
        return '/'.join(parts[4:])
    return None


def raw_url(repo, sha, path):
    return f'https://raw.githubusercontent.com/codrops/{quote(repo)}/{sha}/' + quote(path)


def resolve_preview(item, collected):
    """Return preview fields for one repository item using only api.github.com."""
    repo = urlparse(item['url']).path.strip('/').split('/')[1]
    meta = gh(f'repos/codrops/{repo}')
    branch = meta['default_branch']
    fields = {}
    home = (meta.get('homepage') or '').strip()
    home_host = (urlparse(home).hostname or '').lower()
    if home.startswith('https://') and not is_host(home_host, BLOCKED_HOST) and not item.get('demo'):
        fields['demo'] = home
    try:
        sha = gh(f'repos/codrops/{repo}/commits/{quote(branch, safe="")}', accept='application/vnd.github.sha').strip()
    except GhError as err:
        if err.status != 409:  # 409: empty repository
            raise
        sha = None
    fields.update({'previewCollected': collected})
    if not sha or not re.fullmatch(r'[0-9a-f]{40}', sha):
        fields.update({'preview': f'https://opengraph.githubassets.com/1/codrops/{repo}', 'previewSource': 'github-social-card'})
        return fields
    fields['commit'] = sha
    tree = gh(f'repos/codrops/{repo}/git/trees/{sha}?recursive=1')
    files = {entry['path'] for entry in tree.get('tree', []) if entry.get('type') == 'blob'}
    lower = {path.lower(): path for path in files}
    try:
        readme = gh(f'repos/codrops/{repo}/readme?ref={sha}')
        readme_dir = readme['path'].rpartition('/')[0]
        readme_dir = readme_dir + '/' if readme_dir else ''
        text = base64.b64decode(readme.get('content', '')).decode('utf-8', 'replace')
    except GhError as err:
        if err.status != 404:
            raise
        readme_dir, text = '', ''
    refs = readme_images(text)
    remote = None
    for ref in refs:
        path = repo_path_for(ref, repo, readme_dir)
        if path is not None:
            path = path.split('?')[0].split('#')[0]
            real = path if path in files else lower.get(path.lower())
            if real and IMAGE_EXT.search(real):
                fields.update({'preview': raw_url(repo, sha, real), 'previewSource': 'repository-file', 'previewPath': real})
                return fields
            continue
        parsed = urlparse(ref)
        host = (parsed.hostname or '').lower()
        if remote is None and parsed.scheme in ('http', 'https') and host and not any(is_host(host, skip) for skip in SKIP_HOSTS) \
                and 'badge' not in parsed.path.lower():
            remote = (ref, host)
    for folder in CONVENTIONAL_DIRS:
        for path in sorted(files):
            if path.startswith(folder) and '/' not in path[len(folder):] and CONVENTIONAL.search(path):
                fields.update({'preview': raw_url(repo, sha, path), 'previewSource': 'repository-file', 'previewPath': path})
                return fields
    if remote:
        url, host = remote
        if url.startswith('http://'):  # string rewrite only, avoids mixed content; nothing is requested
            url = 'https://' + url[len('http://'):]
        fields.update({'preview': url, 'previewSource': 'readme-remote', 'previewHost': host})
        return fields
    fields.update({'preview': f'https://opengraph.githubassets.com/1/codrops/{repo}', 'previewSource': 'github-social-card'})
    return fields


def enrich_previews(items, collected, workers=4):
    """Resolve previews for repository items, at most `workers` repositories at a time."""
    repos = [item for item in items if urlparse(item['url']).hostname == 'github.com'
             and urlparse(item['url']).path.lower().startswith('/codrops/')
             # local renders (scripts/render-codrops-previews.mjs) are kept; re-run that script to refresh them
             and item.get('previewSource') != 'local-render']
    for item in repos:
        for field in PREVIEW_FIELDS:
            item.pop(field, None)
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, 4)) as pool:
        futures = {pool.submit(resolve_preview, item, collected): item for item in repos}
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            futures[future].update(future.result())
            if done % 50 == 0:
                print(f'  previews resolved: {done}/{len(repos)}')
    by_article = {item['article']: item for item in repos if item.get('article')}
    for item in items:
        if item['kind'] == 'article-reference' and item['url'] in by_article:
            match = by_article[item['url']]
            item.update({field: match[field] for field in PREVIEW_FIELDS if field in match})
            item['previewFromRepository'] = match['url']
    return repos


def preview_coverage(items, collected):
    counts = {}
    for item in items:
        if item.get('previewSource'):
            counts[item['previewSource']] = counts.get(item['previewSource'], 0) + 1
    return {
        'resolvedOn': collected, 'bySource': dict(sorted(counts.items())),
        'withoutPreview': sum(1 for item in items if not item.get('preview')),
        'method': 'Authenticated GitHub REST API (repository, default-branch commit, recursive tree, README), at most 4 repositories at a time. Repository files are pinned to the default-branch commit SHA on raw.githubusercontent.com. README images on other hosts are stored as URLs for the visitor\'s browser and were not fetched. Remaining repositories use GitHub\'s generated social card.',
        'localRenders': counts.get('local-render', 0),
        'localRenderMethod': 'scripts/render-codrops-previews.mjs: shallow clone of the official repository (no hooks, install or build), static files served on loopback, screenshot in headless Chrome at 1280x800 with tympanus.net and Codrops CDN requests blocked. Commit and entry page recorded per item.',
        'imagesDownloaded': False, 'tympanusRequested': False, 'videosCollected': False,
        'articleReferences': 'No preview unless a repository records the identical article URL; none were inferred.',
    }


def fetch_pages():
    url = API
    pages = []
    while url:
        if urlparse(url).hostname != 'api.github.com':
            raise ValueError('Unexpected pagination host')
        request = urllib.request.Request(url, headers={
            'User-Agent': 'Frontend-Library-reference-index', 'Accept': 'application/vnd.github+json',
        })
        with urllib.request.urlopen(request, timeout=40) as response:
            items = json.load(response)
            if not isinstance(items, list):
                raise ValueError('GitHub response is not a repository list')
            pages.append({'url': url, 'items': items})
            next_link = re.search(r'<([^>]+)>; rel="next"', response.headers.get('Link', ''))
            url = next_link.group(1) if next_link else None
        time.sleep(.6)
    return pages


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def build(pages, previews=False):
    collected = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    items = []
    seen = set()
    for page in pages:
        if urlparse(page['url']).hostname != 'api.github.com':
            raise ValueError('Cache has unexpected source host')
        for repo in page['items']:
            url = repo['html_url']
            if repo.get('owner', {}).get('login', '').lower() != 'codrops' or url in seen:
                continue
            seen.add(url)
            searchable = ' '.join([repo['name'], repo.get('description') or '', *repo.get('topics', [])])
            tags = [tag for tag, pattern in TERMS.items() if re.search(pattern, searchable, re.I)]
            if not tags:
                continue
            ident = slug(repo['name'])
            item = {
                'id': 'codrops-repo-' + ident, 'name': repo['name'], 'url': url,
                'source': page['url'], 'collected': collected, 'kind': 'demo-repository',
                'attribution': 'Codrops and repository contributors',
                'description': repo.get('description') or '', 'tags': tags,
                'tagEvidence': 'Matched repository name, description and GitHub topics; runtime not inspected.',
                'repositoryTopics': repo.get('topics', []), 'code': url,
                'createdAt': repo.get('created_at'), 'updatedAt': repo.get('updated_at'),
                'archived': repo.get('archived', False), 'fork': repo.get('fork', False),
                'license': (repo.get('license') or {}).get('spdx_id') or 'not-declared-in-api',
                'licenseScope': 'Repository API metadata only; verify LICENSE and third-party asset notices before reuse.',
                'evidence': 'linked-repository-metadata', 'animationsCaptured': False,
            }
            home = (repo.get('homepage') or '').strip()
            if home.startswith(('http://', 'https://')):
                field = 'article' if '/codrops/' in home else 'demo'
                item[field] = home
            items.append(item)
    for path, name, tags in ARTICLES:
        url = 'https://tympanus.net/codrops/' + path
        items.append({
            'id': 'codrops-article-' + hashlib.sha256(url.encode()).hexdigest()[:12],
            'name': name, 'url': url, 'source': TAG, 'collected': '2026-11-12',
            'published': path[:10].replace('/', '-'), 'kind': 'article-reference',
            'attribution': 'Codrops and the credited article author(s)',
            'tags': ['WebGL', *tags], 'evidence': 'public-tag-listing-and-search-permalink',
            'animationsCaptured': False, 'license': 'not-verified',
            'description': 'WebGL-tagged article reference. Open through permitted access to inspect the technique and credited author.',
        })
    items.sort(key=lambda item: (item['kind'], item['name'].lower()))
    ids = [item['id'] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate generated IDs')
    previous = load_catalog()
    if previews:
        enrich_previews(items, collected)
    elif previous:
        old = {item['id']: item for item in previous['items']}
        for item in items:
            for field in (*PREVIEW_FIELDS, 'previewFromRepository'):
                if field in old.get(item['id'], {}):
                    item.setdefault(field, old[item['id']][field])
    catalog = {
        'version': 1, 'source': TAG, 'collected': collected, 'count': len(items),
        'coverage': {
            'tagPostsAdvertised': 263, 'tagPagesAdvertised': 13, 'articleReferencesResolved': len(ARTICLES),
            'repositoryPagesRead': [page['url'] for page in pages],
            'repositoryRecordsSeen': sum(len(page['items']) for page in pages),
            'repositoryRecordsUnique': len(seen), 'repositoryRecordsIncluded': len(items)-len(ARTICLES),
            'repositorySelection': 'Name/description/topics match WebGL, Three.js, shader, scroll, transition, hover, 3D, particle, gallery, slideshow, distortion, cursor or animation patterns.',
            'notFullTagArchive': True, 'pageCapturesBundled': False,
        },
        'access': {
            'robotsUrl': 'https://tympanus.net/robots.txt', 'checkedOn': '2026-11-12',
            'contentSignals': 'search=yes,ai-train=no,use=reference',
            'namedAiCrawlerRestriction': 'GPTBot and other named AI crawlers disallowed.',
            'directTagRequest': 'HTTP 403; no bypass attempted.',
            'articleBodiesCrawled': False,
            'alternative': 'Official Codrops public GitHub repository API metadata, fetched sequentially via observed Link pagination.',
        },
        'items': items,
    }
    if any(item.get('preview') for item in items):
        catalog['coverage']['previews'] = preview_coverage(items, (previous or {}).get('coverage', {}).get('previews', {}).get('resolvedOn', collected) if not previews else collected)
        catalog['access']['previewImagesFetched'] = False
    write(catalog)


def load_catalog():
    path = ROOT / 'data/codrops-webgl.json'
    return json.loads(path.read_text()) if path.exists() else None


def cell(text):
    return str(text).replace('|', chr(92) + '|')


def thumb(item, width=96):
    if not item.get('preview'):
        return '—'
    alt = html.escape(f"Preview of {item['name']}", quote=True)
    src = item['preview'] if item['preview'].startswith('https://') else '../../' + item['preview']
    return f'<a href="{html.escape(item["url"], quote=True)}"><img src="{html.escape(src, quote=True)}" width="{width}" alt="{alt}"></a>'


def write(catalog):
    items = catalog['items']
    ARTICLE_COUNT = sum(1 for item in items if item['kind'] == 'article-reference')
    (ROOT / 'data/codrops-webgl.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n')
    previews = catalog['coverage'].get('previews')
    lines = ['# Codrops: WebGL and creative frontend references', '',
             f'**{len(items):,} source-tracked references: {len(items)-ARTICLE_COUNT} official Codrops demo repositories and {ARTICLE_COUNT} resolved WebGL article links.**', '',
             '[Original WebGL tag](https://tympanus.net/codrops/tag/webgl/) · [Machine-readable catalog](../../data/codrops-webgl.json) · [Library](../../README.md)', '',
             'These are links and factual repository metadata, not local landing-page captures. They complement the [Lusion page recordings](../../docs/reference-library/README.md) with implementation references for shaders, scrolling, transitions, typography, galleries and interaction.', '',
             '## Coverage and access', '',
             'The public WebGL tag listing advertised 263 posts across 13 pages on 2026-11-12. Its first listing exposed 18 current article references; their exact permalinks were resolved through public search results. Codrops robots.txt blocks named AI crawlers, and a direct tag request returned HTTP 403. Article bodies and blocked pagination were not bulk-crawled. The remaining collection comes from Codrops’ own public GitHub account, following API pagination sequentially. This is not a claim to have collected all 263 tagged posts.', '',
             'Tags on repository records are metadata matches, not verification of dependencies or runtime techniques. Repository creation dates are not article publication dates. A linked demo is included only when the GitHub API explicitly supplied it as a homepage; no demo URL was guessed.', '',
             *([] if not previews else [
                 '## Previews', '',
                 f"Repository rows show a small preview: {previews['bySource'].get('local-render', 0)} screenshots of the demo rendered locally from its official repository (headless Chrome, tympanus.net requests blocked, commit recorded per row; see `scripts/render-codrops-previews.mjs`), {previews['bySource'].get('repository-file', 0)} images committed in the repository (pinned to the default-branch commit on raw.githubusercontent.com), {previews['bySource'].get('readme-remote', 0)} README images hosted elsewhere (hotlinked by your browser, mostly from tympanus.net; not fetched or stored by this library) and {previews['bySource'].get('github-social-card', 0)} GitHub-generated social cards. Previews were resolved through the GitHub API on {previews['resolvedOn']}; tympanus.net was not requested and no demo videos were collected. Local renders are reference screenshots: the demos, their code and assets belong to Codrops and the demo authors.", '']),
             '## Use with an agent', '',
             'Choose a reference by its tags, then open the repository, its README and its declared demo through permitted access. Inspect the actual effect before adapting it. Verify the current dependency versions, LICENSE and asset notices; an MIT repository may contain separately credited images, fonts or models. Match the user’s project stack and keep layout, motion and assets as distinct implementation requirements. Follow the [frontend-library skill](../../.agents/skills/frontend-library/SKILL.md).', '',
             '## Article references', '', '| Article | Date | Topics |', '|:--|:--|:--|']
    for item in items:
        if item['kind'] == 'article-reference':
            lines.append(f"| [{cell(item['name'])}]({item['url']}) | {item['published']} | {', '.join(item['tags'])} |")
    header = ['Preview'] if previews else []
    lines.extend(['', '## Official demo repositories', '', '| ' + ' | '.join([*header, 'Repository', 'Metadata tags', 'Licence reported by API', 'Explicit homepage']) + ' |',
                  '|' + '|'.join([':--'] * (len(header) + 4)) + '|'])
    for item in items:
        if item['kind'] == 'demo-repository':
            homepage = f"[demo]({item['demo']})" if item.get('demo') else f"[article]({item['article']})" if item.get('article') else '—'
            row = [thumb(item)] if previews else []
            row += [f"[{cell(item['name'])}]({item['url']})", ', '.join(item['tags']), item['license'], homepage]
            lines.append('| ' + ' | '.join(row) + ' |')
    lines.extend(['', '## Refresh', '', '```bash', 'python3 scripts/collect-codrops.py --previews', '```', '',
                  'Uses Python standard library, public GitHub API and a 0.6-second pause between sequential requests. `--previews` (or `--previews-only` for the existing catalog) resolves repository previews through the authenticated `gh api`, four repositories at a time at most; it reads repository metadata, trees and READMEs, never image bytes. GitHub errors and rate limits stop the refresh before replacing the catalog. Article seeds are preserved; this command does not fetch Codrops article pages. All designs, code and media retain their original owners’ rights. No third-party source code or media files are bundled here.'])
    (ROOT / 'inspiration/codrops/README.md').write_text('\n'.join(lines)+'\n')
    print(f'Wrote {len(items)} Codrops references ({len(items)-ARTICLE_COUNT} repositories, {ARTICLE_COUNT} articles)')
    if previews:
        print(f"Previews: {previews['bySource']}; without preview: {previews['withoutPreview']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cache', type=Path, help='Read a previously fetched GitHub API pages JSON instead of network')
    parser.add_argument('--previews', action='store_true', help='Resolve repository previews through gh api')
    parser.add_argument('--previews-only', action='store_true', help='Resolve previews for the existing catalog without re-reading the repository list')
    parser.add_argument('--guide-only', action='store_true', help='Rewrite the guide and preview coverage from the existing catalog (no network)')
    args = parser.parse_args()
    if args.guide_only:
        catalog = load_catalog()
        resolved = (catalog['coverage'].get('previews') or {}).get('resolvedOn') or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        catalog['coverage']['previews'] = preview_coverage(catalog['items'], resolved)
        write(catalog)
        return
    if args.previews_only:
        catalog = load_catalog()
        collected = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        enrich_previews(catalog['items'], collected)
        catalog['coverage']['previews'] = preview_coverage(catalog['items'], collected)
        catalog['access']['previewImagesFetched'] = False
        write(catalog)
        return
    pages = json.loads(args.cache.read_text())['pages'] if args.cache else fetch_pages()
    build(pages, previews=args.previews)


if __name__ == '__main__':
    main()
