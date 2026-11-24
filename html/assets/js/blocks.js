// Hiệu ứng "hiện dần khi cuộn tới lần đầu" cho các khối Smart content (hiện có: thanh tóm tắt
// quy trình .tv-process-map). Chỉ chạy 1 lần. Không có JS / trình duyệt cũ / người dùng tắt hiệu
// ứng -> khối vẫn hiện bình thường (trạng thái ẩn chỉ áp khi <html> có class tv-js).
(() => {
  const els = document.querySelectorAll('.tv-process-map');
  if (!els.length || !('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('tv-js');
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.35 });
  els.forEach((el) => io.observe(el));
})();
