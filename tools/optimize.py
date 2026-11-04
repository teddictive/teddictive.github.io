"""Make the site light: resize big images, give the home grid small thumbnails, lazy-load media.

Usage (from the site folder):
    python3 tools/optimize.py

Safe to run again at any time (e.g. after adding a page). Uses macOS `sips`, no extra installs.
- Every image is first copied untouched to _원본이미지/ (never overwritten there).
- Images in images/ that are still identical to their original are resized to at most
  MAX_SIDE px and re-saved as JPEG quality 80 (PNG keeps its format, GIF is left alone).
- images/thumbs/ gets a small copy of each grid thumbnail, and the grid points to it.
- <img> and video <iframe> tags get loading="lazy" so off-screen media loads on scroll.
"""
import os
import re
import shutil
import subprocess
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(SITE, 'images')
ORIG = os.path.join(SITE, '_원본이미지')
THUMBS = os.path.join(IMG, 'thumbs')
MAX_SIDE = 2000
THUMB_SIDE = 900
QUALITY = '80'


def sips(*args):
    r = subprocess.run(['sips', *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def dims(path):
    out = sips('-g', 'pixelWidth', '-g', 'pixelHeight', path)
    w = int(re.search(r'pixelWidth: (\d+)', out).group(1))
    h = int(re.search(r'pixelHeight: (\d+)', out).group(1))
    return w, h


def shrink(src, dst, side):
    ext = os.path.splitext(src)[1].lower()
    args = []
    if max(dims(src)) > side:
        args += ['-Z', str(side)]
    if ext in ('.jpg', '.jpeg'):
        args += ['-s', 'formatOptions', QUALITY]
    if args:
        sips(*args, src, '--out', dst)
    elif src != dst:
        shutil.copy2(src, dst)


def main():
    if shutil.which('sips') is None:
        sys.exit('이 도구는 macOS의 sips 명령이 필요합니다.')
    os.makedirs(ORIG, exist_ok=True)
    os.makedirs(THUMBS, exist_ok=True)
    log = os.path.join(ORIG, '.optimized')
    seen = set(open(log, encoding='utf-8').read().split('\n')) if os.path.exists(log) else set()
    before = after = 0
    done = 0
    for f in sorted(os.listdir(IMG)):
        p = os.path.join(IMG, f)
        ext = os.path.splitext(f)[1].lower()
        if not os.path.isfile(p) or ext not in ('.jpg', '.jpeg', '.png'):
            continue
        o = os.path.join(ORIG, f)
        if not os.path.exists(o):
            shutil.copy2(p, o)
        if f in seen or os.path.getsize(p) != os.path.getsize(o):
            continue  # already optimized
        before += os.path.getsize(p)
        tmp = p + '.tmp' + ext
        shrink(p, tmp, MAX_SIDE)
        if os.path.exists(tmp) and os.path.getsize(tmp) < os.path.getsize(p):
            os.replace(tmp, p)
        elif os.path.exists(tmp):
            os.remove(tmp)
        after += os.path.getsize(p)
        done += 1
        seen.add(f)
    open(log, 'w', encoding='utf-8').write('\n'.join(sorted(x for x in seen if x)))

    # thumbnails + lazy loading in every page
    pages = [f for f in os.listdir(SITE) if f.endswith('.html')]
    thumb_re = re.compile(r'(<div class="thumb_image[^>]*>\s*<img\b[^>]*?src=")images/(?!thumbs/)([^"]+)"')
    made = set()
    for page in pages:
        path = os.path.join(SITE, page)
        doc = open(path, encoding='utf-8').read()
        new = doc

        def to_thumb(m):
            name = m.group(2)
            t = os.path.join(THUMBS, name)
            if name not in made and not os.path.exists(t):
                src = os.path.join(ORIG, name) if os.path.exists(os.path.join(ORIG, name)) else os.path.join(IMG, name)
                shrink(src, t, THUMB_SIDE)
            made.add(name)
            return m.group(1) + 'images/thumbs/' + name + '"'

        new = thumb_re.sub(to_thumb, new)
        # lazy-load everything except the menu logo (it carries data-scale)
        new = re.sub(r'<img\b(?![^>]*\bloading=)(?![^>]*\bdata-scale=)', '<img loading="lazy"', new)
        new = re.sub(r'<iframe\b(?![^>]*\bloading=)', '<iframe loading="lazy"', new)
        if new != doc:
            open(path, 'w', encoding='utf-8').write(new)

    mb = lambda b: f'{b / 1048576:.1f}MB'
    print(f'이미지 {done}장 최적화: {mb(before)} → {mb(after)}, 썸네일 {len(made)}장, 원본은 _원본이미지/ 에 보관')


if __name__ == '__main__':
    main()
