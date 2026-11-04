// Recreates the behaviour of the original Cargo site:
// height-based type scale, mobile mode, column thumbnails, scroll fade-in,
// image quick view, in-place page navigation and the mobile site menu.
(function () {
	var MOBILE_MAX = 768;
	var html = document.documentElement;

	function isMobile() {
		return window.innerWidth <= MOBILE_MAX;
	}

	// Cargo scales 1rem with the window height (about 0.09% of innerHeight per 1%)
	function setScale() {
		var h = window.innerHeight, w = window.innerWidth;
		var pct = h * 0.09;
		if (isMobile()) pct = Math.min(pct, w * 0.16);
		html.style.fontSize = pct.toFixed(2) + '%';
		document.body.classList.toggle('mobile', isMobile());
		document.body.classList.toggle('full_width', isMobile());
		document.body.classList.toggle('homepage', document.body.dataset.page === 'Home');
	}

	// Cargo's mobile padding setting (-5) halves page and thumbnail padding on mobile
	function mobilePadding() {
		document.querySelectorAll('.content_padding, [thumbnails-pad]').forEach(function (el) {
			el.style.padding = '';
			if (!isMobile()) return;
			var cs = getComputedStyle(el);
			el.style.padding = ['Top', 'Right', 'Bottom', 'Left'].map(function (k) {
				return parseFloat(cs['padding' + k]) / 2 + 'px';
			}).join(' ');
		});
		document.querySelectorAll('[thumbnails]').forEach(function (el) {
			el.style.margin = '';
			if (!isMobile()) return;
			var cs = getComputedStyle(el);
			el.style.margin = ['Top', 'Right', 'Bottom', 'Left'].map(function (k) {
				return parseFloat(cs['margin' + k]) / 2 + 'px';
			}).join(' ');
		});
	}

	// "Columns" thumbnail mode: 3 columns on desktop, 1 on mobile, shortest column first
	function layoutThumbs() {
		document.querySelectorAll('[thumbnails="columns"]').forEach(function (row) {
			var n = isMobile() ? 1 : 3;
			var thumbs = Array.prototype.slice.call(row.querySelectorAll('.thumbnail'));
			if (!thumbs.length) return;
			if (row.dataset.cols == n) return;
			thumbs.sort(function (a, b) { return a.dataset.order - b.dataset.order; });
			var cols = Array.prototype.slice.call(row.querySelectorAll('.column'));
			var tmpl = cols[0];
			cols.forEach(function (c) { c.remove(); });
			var made = [], heights = [];
			for (var i = 0; i < n; i++) {
				var c = tmpl.cloneNode(false);
				c.setAttribute('grid-col', n === 1 ? 'x12' : 'x10');
				row.appendChild(c);
				made.push(c);
				heights.push(0);
			}
			thumbs.forEach(function (t) {
				var k = heights.indexOf(Math.min.apply(null, heights));
				made[k].appendChild(t);
				var box = t.querySelector('.thumb_image');
				var ratio = box ? parseFloat(box.style.paddingBottom) || 100 : 100;
				heights[k] += ratio + 15;
			});
			row.dataset.cols = n;
		});
	}

	// Scroll transition: content fades up as it enters the viewport
	var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
		entries.forEach(function (e) {
			if (e.isIntersecting) {
				e.target.classList.remove('below-viewport');
				io.unobserve(e.target);
			}
		});
	}, { rootMargin: '0px 0px -40px 0px' }) : null;

	function setupFade() {
		document.querySelectorAll('.content .scroll-transition-fade').forEach(function (el) {
			if (!io) return;
			var r = el.getBoundingClientRect();
			if (r.top > window.innerHeight) {
				el.classList.add('below-viewport');
				io.observe(el);
			}
		});
	}

	// Quick view lightbox for .image-zoom images
	var lb, lbImg, list = [], idx = 0;

	function buildLightbox() {
		lb = document.createElement('div');
		lb.className = 'lb';
		lb.innerHTML =
			'<div class="lb__bg"></div>' +
			'<div class="lb__stage"><img class="lb__img" alt=""></div>' +
			'<button class="lb__btn lb__close" aria-label="Close"><svg viewBox="0 0 18 18"><path d="M1 1l16 16M17 1L1 17"/></svg></button>' +
			'<button class="lb__btn lb__prev" aria-label="Previous"><svg viewBox="0 0 18 18"><path d="M12 1L4 9l8 8"/></svg></button>' +
			'<button class="lb__btn lb__next" aria-label="Next"><svg viewBox="0 0 18 18"><path d="M6 1l8 8-8 8"/></svg></button>';
		document.body.appendChild(lb);
		lbImg = lb.querySelector('.lb__img');
		lb.querySelector('.lb__close').onclick = closeLB;
		lb.querySelector('.lb__prev').onclick = function (e) { e.stopPropagation(); show(idx - 1); };
		lb.querySelector('.lb__next').onclick = function (e) { e.stopPropagation(); show(idx + 1); };
		lb.querySelector('.lb__stage').onclick = function (e) {
			if (e.target === lbImg) show(idx + 1); else closeLB();
		};
	}

	function show(i) {
		idx = (i + list.length) % list.length;
		lbImg.src = list[idx].getAttribute('src');
	}

	function openLB(img) {
		list = Array.prototype.slice.call(document.querySelectorAll('.page_content img.image-zoom'));
		lb.classList.toggle('single', list.length < 2);
		show(list.indexOf(img));
		lb.classList.add('open');
		requestAnimationFrame(function () { lb.classList.add('visible'); });
		document.documentElement.style.overflow = 'hidden';
	}

	function closeLB() {
		lb.classList.remove('visible');
		setTimeout(function () { lb.classList.remove('open'); }, 250);
		document.documentElement.style.overflow = '';
	}

	document.addEventListener('keydown', function (e) {
		if (!lb || !lb.classList.contains('open')) return;
		if (e.key === 'Escape') closeLB();
		if (e.key === 'ArrowLeft') show(idx - 1);
		if (e.key === 'ArrowRight') show(idx + 1);
	});

	// In-place navigation between pages (falls back to a normal load when fetch is unavailable)
	function isInternal(a) {
		var h = a.getAttribute('href');
		return h && /^[^:#?\/]+\.html$/.test(h) && !a.target;
	}

	function swapTo(href, push) {
		var main = document.querySelector('.main_container');
		main.classList.add('leaving');
		fetch(href).then(function (r) {
			if (!r.ok) throw new Error(r.status);
			return r.text();
		}).then(function (txt) {
			var doc = new DOMParser().parseFromString(txt, 'text/html');
			var next = doc.querySelector('.main_container');
			setTimeout(function () {
				main.innerHTML = next.innerHTML;
				document.title = doc.title;
				document.body.dataset.page = doc.body.dataset.page;
				document.body.setAttribute('data-page-id', doc.body.getAttribute('data-page-id') || '');
				if (push) history.pushState({ href: href }, '', href);
				window.scrollTo(0, 0);
				init();
				main.classList.remove('leaving');
			}, 200);
		}).catch(function () {
			location.href = href;
		});
	}

	document.addEventListener('click', function (e) {
		var img = e.target.closest && e.target.closest('img.image-zoom');
		if (img && !img.closest('a')) {
			e.preventDefault();
			openLB(img);
			return;
		}
		var a = e.target.closest && e.target.closest('a');
		if (!a) return;
		if (a.id === 'site_menu_button') {
			e.preventDefault();
			toggleMenu();
			return;
		}
		if (isInternal(a) && location.protocol !== 'file:' && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
			e.preventDefault();
			closeMenu();
			if (a.getAttribute('href') !== location.pathname.split('/').pop()) swapTo(a.getAttribute('href'), true);
			else window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	});

	window.addEventListener('popstate', function () {
		swapTo(location.pathname.split('/').pop() || 'index.html', false);
	});

	// Mobile Cargo menu: the homepage plus the pages set to show in the menu
	function toggleMenu() {
		var p = document.getElementById('site_menu_panel_container');
		if (!p) return;
		if (!p.querySelector('#site_menu')) {
			p.innerHTML =
				'<div id="site_menu_panel"><div id="site_menu" class="site_menu">' +
				'<div class="page-link home-link"><a href="index.html">Homepage</a><div class="break"></div></div>' +
				'<div class="page-link"><a href="Information.html">Information</a></div>' +
				'<div class="close">×</div>' +
				'</div></div>';
			p.querySelector('.close').onclick = closeMenu;
		}
		p.style.display = p.style.display === 'block' ? 'none' : 'block';
	}

	function closeMenu() {
		var p = document.getElementById('site_menu_panel_container');
		if (p) p.style.display = 'none';
	}

	function init() {
		setScale();
		mobilePadding();
		layoutThumbs();
		setupFade();
	}

	buildLightbox();
	init();
	var t;
	window.addEventListener('resize', function () {
		clearTimeout(t);
		t = setTimeout(function () {
			setScale();
			mobilePadding();
			layoutThumbs();
		}, 80);
	});
})();
