# teddictive — 직접 호스팅용 사이트 (teddictive.cargo.site 복제)

Cargo 없이 동작하는 정적 사이트입니다. 22개 페이지, 이미지 153장(원본 해상도), 폰트까지 전부 이 폴더 안에 있습니다.
YouTube·Vimeo 영상만 원본처럼 외부 임베드입니다.

## 보기
```
cd ~/Desktop/artist-project/teddictive-site
python3 -m http.server 8770
```
→ 브라우저에서 http://127.0.0.1:8770/
(index.html을 더블클릭해도 열리지만, 그때는 페이지 이동이 일반 새로고침 방식이 됩니다.)

## 올리기
폴더 전체를 GitHub Pages / Netlify / Vercel / Cloudflare Pages 등 정적 호스팅에 그대로 올리면 됩니다.
`_source/` 폴더는 올리지 않아도 됩니다.

## 구조
- `index.html` = 홈, `<페이지주소>.html` = 원본의 각 페이지 (예: `/Hypertaste-2016` → `Hypertaste-2016.html`)
- `404.html` = 원본 404 페이지 (원본 메뉴에 숨어 있던 빈 링크 Lara-Zitko는 원본에서도 404)
- `css/cargo.css` 원본 Cargo 스타일, `css/fonts.css` Karla·Space Mono, `css/clone.css` 복제용 보정
- `js/site.js` 동작 재현:
  - 화면 높이에 맞춰 글자·여백 크기 조절 (원본과 같은 공식)
  - 768px 이하 모바일 모드: 왼쪽 메뉴 숨김, 썸네일 1열, 여백 절반, 오른쪽 아래 메뉴 버튼
  - 썸네일 3열 배치, 스크롤 시 이미지가 아래에서 페이드인
  - 이미지 클릭 시 검은 배경 확대 보기 (← → 키, ESC, 좌우 화살표, X)
  - 새로고침 없이 페이지 전환 (뒤로 가기 지원), 현재 페이지 메뉴는 흐리게 표시

## 내용 수정
- 글·이미지는 각 html의 `<bodycopy>` 안을 직접 고치면 됩니다. 새 이미지는 `images/`에 넣고 `<img src="images/파일명">`.
- 이미지 확대가 되게 하려면 img에 `class="image-zoom scroll-transition-fade"`를 붙이세요.
- `_source/build.py`는 2026-11-04에 받아 둔 원본 데이터로 html을 다시 만듭니다. 실행하면 직접 고친 내용이 덮어써지니 주의하세요.
