#!/usr/bin/env python3
"""Pull the product's OWN brand from its source so the video is tailored to it: colours (CSS variables,
Tailwind theme, @theme blocks, theme-color), fonts (Google Fonts links, next/font, @font-face,
font-family declarations), and logo / icon / photo candidates.

  python3 brand_tokens.py <repo> [--out brief/brand.json]

Read the output, then decide the roles (page, ink, accent, dark studio tint, display font, UI font,
logo file) in brief/brief.md, and wire them into edit.json's "theme". This script only gathers
evidence; you still have to look at the real screens to see which colour is the accent.
"""
import os, re, sys, json, collections, base64

repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
SKIP = {'node_modules', '.git', 'dist', 'build', '.next', 'out', 'coverage', '.turbo', '.vercel', 'promo-video', 'vendor', '.cache'}
TEXT = ('.css', '.scss', '.sass', '.less', '.html', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.astro', '.json', '.mjs', '.cjs')
IMG = ('.svg', '.png', '.webp', '.jpg', '.jpeg', '.ico', '.avif')

files = []
for root, dirs, fs in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
    for f in fs: files.append(os.path.join(root, f))
rel = lambda p: os.path.relpath(p, repo)
def read(p):
    try:
        if os.path.getsize(p) > 600_000: return ''
        return open(p, encoding='utf-8', errors='ignore').read()
    except Exception: return ''

HEX = r'#(?:[0-9a-fA-F]{3}){1,2}\b'
css_vars = collections.OrderedDict(); tw_colors = collections.OrderedDict(); hex_count = collections.Counter()
fonts = collections.Counter(); font_links = set(); font_faces = []; theme_color = set(); logos = []; photos = []
for p in files:
    ext = os.path.splitext(p)[1].lower(); name = os.path.basename(p).lower()
    if ext in IMG:
        if re.search(r'logo|brand|wordmark|mark|icon|favicon|apple-touch|og[-_]?image|social', name): logos.append(rel(p))
        elif ext in ('.png', '.webp', '.jpg', '.jpeg', '.avif') and os.path.getsize(p) > 15_000: photos.append(rel(p))
        continue
    if ext not in TEXT: continue
    s = read(p)
    if not s: continue
    for m in re.finditer(r'(--[\w-]+)\s*:\s*(' + HEX + r'|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\))', s):
        css_vars.setdefault(m.group(1), (m.group(2), rel(p)))
    if re.search(r'tailwind\.config', name) or '@theme' in s:
        for m in re.finditer(r"['\"]?([\w-]+)['\"]?\s*:\s*['\"](" + HEX + r")['\"]", s): tw_colors.setdefault(m.group(1), (m.group(2), rel(p)))
    for h in re.findall(HEX, s): hex_count[h.upper()] += 1
    for m in re.finditer(r'fonts\.googleapis\.com/css2?\?[^"\'\s)>]+', s): font_links.add(m.group(0).replace('&amp;', '&'))
    for m in re.finditer(r"from\s+['\"]next/font/google['\"]", s):
        for n in re.findall(r'import\s*{([^}]*)}\s*from\s*[\'"]next/font/google', s): [fonts.update([x.strip().replace('_', ' ')]) for x in n.split(',') if x.strip()]
    for m in re.finditer(r'@font-face\s*{([^}]*)}', s):
        fam = re.search(r'font-family\s*:\s*([^;]+)', m.group(1)); src = re.findall(r'url\(([^)]+)\)', m.group(1))
        font_faces.append({'family': fam.group(1).strip(' "\'') if fam else '?', 'src': [x.strip(' "\'') for x in src][:3], 'file': rel(p)})
    for m in re.finditer(r'font-family\s*:\s*([^;}{]+)', s):
        first = m.group(1).split(',')[0].strip(" '\"")
        if first and not first.startswith('var(') and first.lower() not in ('inherit', 'initial', 'sans-serif', 'serif', 'monospace', 'system-ui'): fonts[first] += 1
    for m in re.finditer(r"(?:font-\[['\"]?|fontFamily[^:]*:\s*\[?\s*['\"])([A-Z][\w ]+?)['\",\]]", s): fonts[m.group(1).strip()] += 1
    for m in re.finditer(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', s): theme_color.add(m.group(1))
    for m in re.finditer(r'<link[^>]+rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*href=["\']([^"\']+)', s): logos.append('icon href: ' + m.group(1)[:200])
google = []
for l in font_links:
    for fam in re.findall(r'family=([^&:]+)', l): google.append(fam.replace('+', ' '))

res = {
  'repo': repo,
  'fonts': {'google_fonts_links': sorted(font_links), 'google_families': sorted(set(google)), 'font_face': font_faces[:12],
            'font_family_usage': fonts.most_common(12)},
  'colors': {'css_variables': {k: v[0] for k, v in list(css_vars.items())[:80]}, 'theme_keys': {k: v[0] for k, v in list(tw_colors.items())[:60]},
             'theme_color_meta': sorted(theme_color), 'most_used_hex': hex_count.most_common(16)},
  'logo_candidates': logos[:40], 'photo_candidates': sorted(photos)[:40],
}
txt = json.dumps(res, indent=1)
if out:
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True); open(out, 'w').write(txt); print('wrote', out)
print(txt)
