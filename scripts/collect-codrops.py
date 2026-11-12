#!/usr/bin/env python3
"""Index public Codrops GitHub demo metadata; do not crawl blocked Codrops pages.

python3 scripts/collect-codrops.py [--cache /path/to/github-pages.json]
The optional cache contains {'pages': [{'url': 'GitHub API URL', 'items': [...]}]}.
"""
import argparse
import datetime
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

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


def build(pages):
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
    (ROOT / 'data/codrops-webgl.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n')
    lines = ['# Codrops: WebGL and creative frontend references', '',
             f'**{len(items):,} source-tracked references: {len(items)-len(ARTICLES)} official Codrops demo repositories and {len(ARTICLES)} resolved WebGL article links.**', '',
             '[Original WebGL tag](https://tympanus.net/codrops/tag/webgl/) · [Machine-readable catalog](../../data/codrops-webgl.json) · [Library](../../README.md)', '',
             'These are links and factual repository metadata, not local landing-page captures. They complement the [Lusion page recordings](../../docs/reference-library/README.md) with implementation references for shaders, scrolling, transitions, typography, galleries and interaction.', '',
             '## Coverage and access', '',
             'The public WebGL tag listing advertised 263 posts across 13 pages on 2026-11-12. Its first listing exposed 18 current article references; their exact permalinks were resolved through public search results. Codrops robots.txt blocks named AI crawlers, and a direct tag request returned HTTP 403. Article bodies and blocked pagination were not bulk-crawled. The remaining collection comes from Codrops’ own public GitHub account, following API pagination sequentially. This is not a claim to have collected all 263 tagged posts.', '',
             'Tags on repository records are metadata matches, not verification of dependencies or runtime techniques. Repository creation dates are not article publication dates. A linked demo is included only when the GitHub API explicitly supplied it as a homepage; no demo URL was guessed.', '',
             '## Use with an agent', '',
             'Choose a reference by its tags, then open the repository, its README and its declared demo through permitted access. Inspect the actual effect before adapting it. Verify the current dependency versions, LICENSE and asset notices; an MIT repository may contain separately credited images, fonts or models. Match the user’s project stack and keep layout, motion and assets as distinct implementation requirements. Follow the [frontend-library skill](../../.agents/skills/frontend-library/SKILL.md).', '',
             '## Article references', '', '| Article | Date | Topics |', '|:--|:--|:--|']
    for item in items:
        if item['kind'] == 'article-reference':
            lines.append(f"| [{item['name'].replace('|', chr(92)+'|')}]({item['url']}) | {item['published']} | {', '.join(item['tags'])} |")
    lines.extend(['', '## Official demo repositories', '', '| Repository | Metadata tags | Licence reported by API | Explicit homepage |', '|:--|:--|:--|:--|'])
    for item in items:
        if item['kind'] == 'demo-repository':
            homepage = f"[demo]({item['demo']})" if item.get('demo') else f"[article]({item['article']})" if item.get('article') else '—'
            lines.append(f"| [{item['name']}]({item['url']}) | {', '.join(item['tags'])} | {item['license']} | {homepage} |")
    lines.extend(['', '## Refresh', '', '```bash', 'python3 scripts/collect-codrops.py', '```', '',
                  'Uses Python standard library, public GitHub API and a 0.6-second pause between sequential requests. GitHub errors and rate limits stop the refresh before replacing the catalog. Article seeds are preserved; this command does not fetch Codrops article pages. All designs, code and media retain their original owners’ rights. No third-party source code or media files are bundled here.'])
    (ROOT / 'inspiration/codrops/README.md').write_text('\n'.join(lines)+'\n')
    print(f'Wrote {len(items)} Codrops references ({len(items)-len(ARTICLES)} repositories, {len(ARTICLES)} articles)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, help='Read a previously fetched GitHub API pages JSON instead of network')
    args = parser.parse_args()
    pages = json.loads(args.cache.read_text())['pages'] if args.cache else fetch_pages()
    build(pages)


if __name__ == '__main__':
    main()
