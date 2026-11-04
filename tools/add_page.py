"""Add a new work page to the site.

Usage (from the site folder):
    python3 tools/add_page.py 새페이지/<folder>

The folder holds:
    info.txt     주소 / 제목 / 메뉴이름 / 위치 (see README)
    본문.txt     text; a line like [이미지 01.jpg], [유튜브 <id or url>] or [비메오 <id or url>] places media
    images       jpg / png / gif, shown in file-name order unless placed in 본문.txt
    썸네일.jpg   optional thumbnail for the home grid (otherwise the first image is used)

It creates <주소>.html, copies the images into images/, and adds the menu link and the
thumbnail to every page. Only the Python standard library is used.
"""
import html
import os
import re
import shutil
import struct
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = 'Hypertaste-2016.html'
IMG_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp')


def image_size(path):
    with open(path, 'rb') as f:
        head = f.read(32)
        if head.startswith(b'\x89PNG'):
            return struct.unpack('>II', head[16:24])
        if head[:6] in (b'GIF87a', b'GIF89a'):
            return struct.unpack('<HH', head[6:10])
        if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
            f.seek(12)
            chunk = f.read(4)
            f.seek(26 if chunk == b'VP8 ' else 21)
            if chunk == b'VP8 ':
                w, h = struct.unpack('<HH', f.read(4))
                return w & 0x3fff, h & 0x3fff
            if chunk == b'VP8L':
                b = f.read(4)
                v = int.from_bytes(b, 'little')
                return (v & 0x3fff) + 1, ((v >> 14) & 0x3fff) + 1
            f.seek(24)
            b = f.read(6)
            return int.from_bytes(b[0:3], 'little') + 1, int.from_bytes(b[3:6], 'little') + 1
        if head[:2] == b'\xff\xd8':
            f.seek(2)
            while True:
                marker = f.read(2)
                if len(marker) < 2:
                    break
                if marker[0] != 0xFF:
                    break
                if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(3)
                    h, w = struct.unpack('>HH', f.read(4))
                    return w, h
                size = struct.unpack('>H', f.read(2))[0]
                f.seek(size - 2, 1)
    return 1000, 1000


def read_info(folder):
    info = {}
    for line in open(os.path.join(folder, 'info.txt'), encoding='utf-8'):
        if ':' in line:
            k, v = line.split(':', 1)
            info[k.strip()] = v.strip()
    for k in ('주소', '제목', '메뉴이름'):
        if not info.get(k):
            sys.exit(f'info.txt 에 "{k}:" 줄이 비어 있습니다.')
    slug = info['주소']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', slug):
        sys.exit('주소는 영문, 숫자, - , _ 만 쓸 수 있습니다. 예) My-New-Work-2026')
    return info


def video(kind, ref):
    ref = ref.strip()
    if kind == '유튜브':
        m = re.search(r'(?:v=|youtu\.be/|embed/)([\w-]{6,})', ref)
        vid = m.group(1) if m else ref
        return (f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{vid}" frameborder="0" '
                'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                'allowfullscreen></iframe>')
    m = re.search(r'(\d{5,})', ref)
    vid = m.group(1) if m else ref
    return (f'<iframe src="https://player.vimeo.com/video/{vid}" width="640" height="360" frameborder="0" '
            'allow="autoplay; fullscreen" allowfullscreen></iframe>')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = os.path.abspath(sys.argv[1])
    info = read_info(folder)
    slug, title, menu = info['주소'], info['제목'], info['메뉴이름']
    after = info.get('위치', '').replace('.html', '').strip()
    out = os.path.join(SITE, slug + '.html')
    if os.path.exists(out):
        sys.exit(f'{slug}.html 이 이미 있습니다. 다른 주소를 쓰거나 기존 파일을 지우세요.')

    # copy images
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT))
    thumb_src = next((f for f in files if os.path.splitext(f)[0] == '썸네일'), None)
    body_imgs = [f for f in files if f != thumb_src]
    local = {}
    for f in files:
        name = slug + '_' + re.sub(r'[^A-Za-z0-9._-]', '_', f)
        if f == thumb_src:
            name = slug + '_thumb' + os.path.splitext(f)[1].lower()
        shutil.copy2(os.path.join(folder, f), os.path.join(SITE, 'images', name))
        local[f] = 'images/' + name

    def img_tag(f):
        w, h = image_size(os.path.join(folder, f))
        return (f'<img border="0" class="image-zoom scroll-transition-fade" decoding="async" '
                f'width="{w}" height="{h}" src="{local[f]}"/>')

    # page body
    parts, used = [], set()
    text_path = os.path.join(folder, '본문.txt')
    lines = open(text_path, encoding='utf-8').read().splitlines() if os.path.exists(text_path) else []
    for line in lines:
        m = re.fullmatch(r'\s*\[(이미지|유튜브|비메오)\s+(.+?)\]\s*', line)
        if m and m.group(1) == '이미지':
            f = m.group(2).strip()
            if f not in local:
                sys.exit(f'본문.txt 의 [이미지 {f}] 파일이 폴더에 없습니다.')
            parts.append(img_tag(f) + '<br/>')
            used.add(f)
        elif m:
            parts.append(video(m.group(1), m.group(2)) + '<br/>')
        else:
            parts.append(html.escape(line) + '<br/>')
    for f in body_imgs:
        if f not in used:
            parts.append(img_tag(f) + '<br/>')
    content = '\n'.join(parts)

    # thumbnail markup
    tf = thumb_src or (body_imgs[0] if body_imgs else None)
    if not tf:
        sys.exit('이미지가 하나도 없습니다. 썸네일로 쓸 이미지를 넣어주세요.')
    tw, th = image_size(os.path.join(folder, tf))
    ratio = round(th / tw * 100, 3)
    pages = sorted(f for f in os.listdir(SITE) if f.endswith('.html') and f != '404.html')

    # order of the new thumbnail in the home grid
    orders = {}
    idx = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
    for m in re.finditer(r'<div class="thumbnail[^"]*" data-id="[^"]*" data-order="([-\d.]+)"[^>]*>\s*<a class="image-link" href="([^"]+)"', idx):
        orders[m.group(2)] = float(m.group(1))
    if after and after + '.html' in orders:
        order = orders[after + '.html'] - 0.5
    else:
        order = min(orders.values() or [0]) - 1
    order_s = ('%g' % order)

    def thumb(active):
        cls = 'thumbnail has_title active' if active else 'thumbnail has_title'
        return (f'<div class="{cls}" data-id="{slug}" data-order="{order_s}" thumbnails-pad="">\n'
                f'<a class="image-link" href="{slug}.html" rel="history">\n'
                f'<div class="thumb_image scroll-transition-fade" style="height: 0px; padding-bottom: {ratio}%;">\n'
                f'<img decoding="async" width="{tw}" height="{th}" src="{local[tf]}" style="width: 100%; height: auto;"/></div>\n'
                f'<div class="title"><span>{html.escape(title)}</span></div>\n'
                f'</a>\n</div>\n')

    def nav(active):
        cls = ' class="active"' if active else ''
        return f'<a{cls} href="{slug}.html" rel="history">{html.escape(menu)}</a><br/>\n'

    def add_shared(doc, active):
        # menu link: before the target page's link, else before the first work link
        target = re.search(r'<a(?: class="active")? href="%s\.html" rel="history">' % re.escape(after), doc) if after else None
        if not target:
            target = re.search(r'<a(?: class="active")? href="[^"]+\.html" rel="history">[^<]+</a>', doc)
        doc = doc[:target.start()] + nav(active) + doc[target.start():]
        # thumbnail: first column of the grid (site.js sorts by data-order)
        col = re.search(r'<div class="column"[^>]*>\s*', doc)
        if col:
            doc = doc[:col.end()] + thumb(active) + doc[col.end():]
        return doc

    # new page from the template
    tpl = open(os.path.join(SITE, TEMPLATE), encoding='utf-8').read()
    tpl = tpl.replace(' class="active"', '').replace('thumbnail has_title active', 'thumbnail has_title')
    tpl = re.sub(r'<title>.*?</title>', f'<title>{html.escape(title)} - teddictive</title>', tpl, count=1)
    tpl = tpl.replace(f'data-page="{TEMPLATE[:-5]}"', f'data-page="{slug}"')
    main_at = tpl.index('data-container="page"')
    start = re.compile(r'<div class="page_content clearfix"[^>]*>').search(tpl, main_at)
    end = tpl.index('</div>', start.end())
    # the template's page_content holds no nested divs, so its first </div> closes it
    tpl = tpl[:start.end()] + '\n' + content + '\n' + tpl[end:]

    # build everything first so a failure leaves the site untouched
    updated = {os.path.join(SITE, p): add_shared(open(os.path.join(SITE, p), encoding='utf-8').read(), False)
               for p in pages}
    updated[out] = add_shared(tpl, True)
    for path, doc in updated.items():
        open(path, 'w', encoding='utf-8').write(doc)

    print(f'완료: {slug}.html 생성, 이미지 {len(files)}장 복사, 메뉴와 썸네일을 {len(pages) + 1}개 페이지에 추가')
    # shrink the new images and make the grid thumbnail (originals go to _원본이미지/)
    if shutil.which('sips'):
        import subprocess
        subprocess.run([sys.executable, os.path.join(SITE, 'tools', 'optimize.py')])


if __name__ == '__main__':
    main()
