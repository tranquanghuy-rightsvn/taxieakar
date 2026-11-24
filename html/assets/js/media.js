// Khối ảnh + video của Smart content:
//  - .tv-gallery[data-gallery]: dải ảnh trượt ngang, nút ‹ ›, bấm ảnh để phóng to (xem ảnh lớn ở data-full)
//  - .tv-video[data-video]: ảnh chờ phủ đầy khung + nút Play; video để preload="none" nên KHÔNG tải
//    gì cho tới khi người xem bấm Play, và không tự chạy.
// Không có JS: dải ảnh vẫn vuốt ngang được, video vẫn có sẵn trong trang.
(() => {
  // ---------- Slider ảnh ----------
  document.querySelectorAll('.tv-gallery[data-gallery]').forEach((g) => {
    const track = g.querySelector('.tv-gallery-track');
    const prev = g.querySelector('.tv-gallery-btn--prev');
    const next = g.querySelector('.tv-gallery-btn--next');
    if (!track) return;
    const step = () => {
      const item = track.querySelector('.tv-gallery-item');
      return item ? item.getBoundingClientRect().width + 12 : track.clientWidth;
    };
    const update = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    };
    if (prev) prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    if (next) next.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  });

  // ---------- Phóng to ảnh ----------
  let box = null, list = [], idx = 0, startX = null;
  const icon = (d) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
  function show() {
    const it = list[idx];
    const img = box.querySelector('img');
    img.src = it.full;
    img.alt = it.alt;
    box.querySelector('.tv-lightbox-cap').textContent = (idx + 1) + ' / ' + list.length + (it.cap ? '  ·  ' + it.cap : '');
  }
  function close() {
    if (!box) return;
    box.remove();
    box = null;
    document.removeEventListener('keydown', onKey);
    document.documentElement.style.overflow = '';
  }
  function move(d) { idx = (idx + d + list.length) % list.length; show(); }
  function onKey(e) {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') move(-1);
    else if (e.key === 'ArrowRight') move(1);
  }
  function open(items, i, wm) {
    list = items; idx = i;
    box = document.createElement('div');
    box.className = 'tv-lightbox' + (wm ? ' tv-lightbox--wm' : '');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<span class="tv-lightbox-frame"><img alt=""></span><p class="tv-lightbox-cap"></p>' +
      '<button type="button" class="tv-lightbox-close" aria-label="Đóng">' + icon('<path d="M18 6 6 18M6 6l12 12"/>') + '</button>' +
      (items.length > 1
        ? '<button type="button" class="tv-lightbox-prev" aria-label="Ảnh trước">' + icon('<path d="m15 18-6-6 6-6"/>') + '</button>' +
          '<button type="button" class="tv-lightbox-next" aria-label="Ảnh tiếp theo">' + icon('<path d="m9 18 6-6-6-6"/>') + '</button>'
        : '');
    box.addEventListener('click', (e) => {
      if (e.target === box) close();
      else if (e.target.closest('.tv-lightbox-close')) close();
      else if (e.target.closest('.tv-lightbox-prev')) move(-1);
      else if (e.target.closest('.tv-lightbox-next')) move(1);
    });
    box.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
    box.addEventListener('touchend', (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) move(dx < 0 ? 1 : -1);
      startX = null;
    });
    document.body.appendChild(box);
    document.documentElement.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey);
    show();
    requestAnimationFrame(() => box && box.classList.add('is-open'));
    const btn = box.querySelector('.tv-lightbox-close');
    if (btn) btn.focus();
  }
  // Nhóm ảnh bấm phóng to: dải ảnh tv-gallery, thẻ công trình tv-proof (chú thích = tên công trình), bản vẽ tv-plan
  document.querySelectorAll('.tv-gallery[data-gallery], .tv-proof[data-gallery], .tv-plan[data-gallery]').forEach((g) => {
    const medias = Array.prototype.slice.call(g.querySelectorAll('.tv-gallery-media, .tv-proof-media, .tv-plan-media'));
    const wm = !!g.closest('.tv-wm'); // bài có gắn logo góc phải lên ảnh: ảnh phóng to cũng có logo
    const items = medias.map((m) => {
      const img = m.querySelector('img');
      const card = m.closest('.tv-proof-card');
      const cap = card ? card.querySelector('h3') : m.parentNode.querySelector('.tv-gallery-cap, .tv-plan-cap');
      return { full: m.getAttribute('data-full') || (img && img.currentSrc) || (img && img.src), alt: img ? img.alt : '', cap: cap ? cap.textContent.trim() : '' };
    });
    medias.forEach((m, i) => {
      m.setAttribute('role', 'button');
      m.setAttribute('tabindex', '0');
      m.setAttribute('aria-label', 'Phóng to ảnh ' + (i + 1));
      m.addEventListener('click', () => open(items, i, wm));
      m.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(items, i, wm); } });
    });
  });

  // ---------- Video: bấm mới tải + phát ----------
  document.querySelectorAll('.tv-video[data-video]').forEach((w) => {
    const video = w.querySelector('video');
    const cover = w.querySelector('.tv-video-cover');
    if (!video || !cover) return;
    cover.addEventListener('click', () => {
      document.querySelectorAll('.tv-video video').forEach((v) => { if (v !== video) v.pause(); });
      video.controls = true;
      w.classList.add('is-playing');
      const p = video.play();
      if (p && p.catch) p.catch(() => { /* trình duyệt chặn phát: vẫn còn nút phát của video */ });
    });
  });
})();
