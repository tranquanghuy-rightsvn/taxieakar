/**
 * Gửi form công khai lên backend CMS:
 *   - Đặt xe: widget "ĐẶT XE NHANH" (#quickBookingForm) chỉ có điểm đón / điểm đến / thời gian.
 *     Bấm "ĐẶT XE NGAY" -> mở POPUP hỏi Họ tên + Số điện thoại -> bấm xác nhận mới gửi đơn
 *     hoàn chỉnh (GAS.md mục VI).
 *   - Đăng ký nhận tư vấn: form #dangkyForm (Họ tên, SĐT, Địa chỉ) - có ở nhiều trang.
 *
 * Vì sao dùng fetch() chứ không phải submit thường: backend nằm ở domain khác, và phải trả
 * lời ngay trên trang (không điều hướng đi đâu).
 *
 * ⚠️ Content-Type BẮT BUỘC là "text/plain;charset=utf-8" — giữ request ở dạng "simple
 * request" nên trình duyệt KHÔNG gửi OPTIONS preflight trước. Backend không xử lý được
 * OPTIONS, đổi sang application/json là hỏng ngay bằng lỗi CORS.
 *
 * Mỗi form đều có 1 ô bẫy bot tên "_hp" ẩn bằng CSS (.hp-field trong style.css). Người thật
 * không bao giờ thấy nên luôn để trống; bot điền tự động thì server âm thầm bỏ qua.
 */
(function () {
  'use strict';

  var ENDPOINT =
    'https://script.google.com/macros/s/AKfycbzwzz_Iqlxki0UAy6MI5FEE2AIVyR3ccKNru5Kw1BSQQrs3Tv0-aew9IY2Py6wN6sg6pA/exec';

  var HOTLINE = '0856 713 714';

  var ICON_SUCCESS =
    '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" ' +
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M20 6L9 17l-5-5"/></svg>';
  var ICON_ERROR =
    '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" ' +
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M12 8v5M12 17h.01"/><circle cx="12" cy="12" r="9"/></svg>';
  var ICON_SPINNER =
    '<svg class="btn-spinner" viewBox="0 0 24 24" width="16" height="16" fill="none" ' +
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">' +
    '<path d="M12 3a9 9 0 1 0 9 9"/></svg>';
  var ICON_CLOSE =
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  /** Trang đang gửi form = thư mục đầu của URL ("/" là trang chủ). Server tự kiểm lại. */
  function currentSource() {
    var seg = location.pathname.replace(/^\/+/, '').split('/')[0];
    return seg ? seg.replace(/\.html$/, '') : 'trang-chu';
  }

  /** Số điện thoại VN: 0xxxxxxxxx hoặc +84xxxxxxxxx, cho phép khoảng trắng/chấm/gạch ngang. */
  function isValidPhone(raw) {
    var d = String(raw || '').replace(/[^\d+]/g, '');
    return /^(0\d{9}|\+84\d{9}|84\d{9})$/.test(d);
  }

  function val(form, name) {
    var el = form.querySelector('[name="' + name + '"]');
    return el ? String(el.value || '').trim() : '';
  }

  function setButtonLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
      if (!btn.hasAttribute('data-original-html')) {
        btn.setAttribute('data-original-html', btn.innerHTML);
      }
      btn.disabled = true;
      btn.classList.add('is-loading');
      btn.innerHTML = ICON_SPINNER + '<span>Đang gửi...</span>';
    } else {
      btn.disabled = false;
      btn.classList.remove('is-loading');
      var original = btn.getAttribute('data-original-html');
      if (original !== null) btn.innerHTML = original;
    }
  }

  function send(payload) {
    return fetch(ENDPOINT, {
      method: 'POST',
      // Không đổi thành application/json — xem ghi chú đầu file.
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        return res.json();
      })
      .catch(function () {
        // Lỗi mạng / backend chưa sẵn sàng — không để form "im lặng không phản hồi".
        return { ok: false, error: 'Không gửi được, quý khách vui lòng gọi hotline ' + HOTLINE + ' giúp em.' };
      });
  }

  // ------------------------------------------------------------ popup kết quả

  var resultOverlay = null;
  var resultLastFocused = null;

  function buildResultModal() {
    if (resultOverlay) return resultOverlay;
    resultOverlay = document.createElement('div');
    resultOverlay.className = 'form-modal-overlay';
    resultOverlay.setAttribute('role', 'dialog');
    resultOverlay.setAttribute('aria-modal', 'true');
    resultOverlay.setAttribute('aria-labelledby', 'formModalTitle');
    resultOverlay.hidden = true;
    resultOverlay.innerHTML =
      '<div class="form-modal">' +
      '<div class="form-modal-icon"></div>' +
      '<h3 class="form-modal-title" id="formModalTitle"></h3>' +
      '<p class="form-modal-text"></p>' +
      '<button type="button" class="form-modal-ok">OK</button>' +
      '</div>';
    document.body.appendChild(resultOverlay);

    resultOverlay.querySelector('.form-modal-ok').addEventListener('click', closeResultModal);
    resultOverlay.addEventListener('click', function (e) {
      if (e.target === resultOverlay) closeResultModal();
    });
    return resultOverlay;
  }

  function openOverlay(el) {
    el.hidden = false;
    // Đọc offsetWidth ép trình duyệt vẽ trạng thái đầu trước khi thêm class -> transition chạy.
    void el.offsetWidth;
    el.classList.add('is-open');
  }

  function closeOverlay(el, after) {
    el.classList.remove('is-open');
    window.setTimeout(function () {
      el.hidden = true;
      if (after) after();
    }, 180);
  }

  function showResult(type, title, text) {
    var el = buildResultModal();
    el.querySelector('.form-modal').className = 'form-modal form-modal--' + type;
    el.querySelector('.form-modal-icon').innerHTML = type === 'success' ? ICON_SUCCESS : ICON_ERROR;
    el.querySelector('.form-modal-title').textContent = title;
    el.querySelector('.form-modal-text').textContent = text;
    resultLastFocused = document.activeElement;
    openOverlay(el);
    el.querySelector('.form-modal-ok').focus();
  }

  function closeResultModal() {
    if (!resultOverlay || resultOverlay.hidden) return;
    closeOverlay(resultOverlay, function () {
      if (resultLastFocused && typeof resultLastFocused.focus === 'function') resultLastFocused.focus();
    });
  }

  // ------------------------------------------------------------ popup đặt xe

  var bookingOverlay = null;
  var bookingWidget = null;

  function buildBookingModal() {
    if (bookingOverlay) return bookingOverlay;
    bookingOverlay = document.createElement('div');
    bookingOverlay.className = 'form-modal-overlay';
    bookingOverlay.setAttribute('role', 'dialog');
    bookingOverlay.setAttribute('aria-modal', 'true');
    bookingOverlay.setAttribute('aria-labelledby', 'bookingModalTitle');
    bookingOverlay.hidden = true;
    bookingOverlay.innerHTML =
      '<form class="form-modal booking-modal" novalidate>' +
      '<button type="button" class="booking-modal-close" aria-label="Đóng">' + ICON_CLOSE + '</button>' +
      '<h3 class="form-modal-title" id="bookingModalTitle">Xác nhận đặt xe</h3>' +
      '<p class="booking-modal-sub">Để lại họ tên và số điện thoại, tổng đài sẽ gọi lại xác nhận chuyến đi ngay.</p>' +
      '<div class="booking-modal-trip"></div>' +
      '<div class="form-group">' +
      '<label for="bm-name">Họ và tên</label>' +
      '<input type="text" id="bm-name" name="name" placeholder="Nhập họ và tên" autocomplete="name">' +
      '</div>' +
      '<div class="form-group">' +
      '<label for="bm-phone">Số điện thoại</label>' +
      '<input type="tel" id="bm-phone" name="phone" placeholder="Nhập số điện thoại" autocomplete="tel" inputmode="tel">' +
      '</div>' +
      '<div class="hp-field" aria-hidden="true"><label>Website<input type="text" name="_hp" tabindex="-1" autocomplete="off"></label></div>' +
      '<p class="booking-modal-error" role="alert" hidden></p>' +
      '<button type="submit" class="contact-submit booking-modal-submit">XÁC NHẬN ĐẶT XE</button>' +
      '</form>';
    document.body.appendChild(bookingOverlay);

    var form = bookingOverlay.querySelector('form');
    bookingOverlay.querySelector('.booking-modal-close').addEventListener('click', closeBookingModal);
    bookingOverlay.addEventListener('click', function (e) {
      if (e.target === bookingOverlay) closeBookingModal();
    });
    form.addEventListener('submit', onBookingConfirm);
    return bookingOverlay;
  }

  function tripSummary(widget) {
    var pickup = val(widget, 'pickup');
    var dropoff = val(widget, 'dropoff');
    var time = val(widget, 'pickup_time');
    var parts = [];
    if (pickup || dropoff) parts.push((pickup || '…') + ' → ' + (dropoff || '…'));
    if (time) {
      var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(time);
      parts.push(m ? m[4] + ':' + m[5] + ' ngày ' + m[3] + '/' + m[2] + '/' + m[1] : time);
    }
    return parts.join(' · ');
  }

  function setBookingError(msg) {
    var el = bookingOverlay.querySelector('.booking-modal-error');
    el.textContent = msg || '';
    el.hidden = !msg;
  }

  function openBookingModal(widget) {
    bookingWidget = widget;
    var el = buildBookingModal();
    var trip = el.querySelector('.booking-modal-trip');
    var summary = tripSummary(widget);
    trip.textContent = summary;
    trip.hidden = !summary;
    setBookingError('');
    openOverlay(el);
    el.querySelector('[name="name"]').focus();
  }

  function closeBookingModal() {
    if (!bookingOverlay || bookingOverlay.hidden) return;
    closeOverlay(bookingOverlay);
  }

  function onBookingConfirm(e) {
    e.preventDefault();
    var form = e.currentTarget;
    var widget = bookingWidget;
    var name = val(form, 'name');
    var phone = val(form, 'phone');
    if (!name) { setBookingError('Quý khách vui lòng nhập họ tên để tổng đài gọi lại xác nhận.'); return; }
    if (!isValidPhone(phone)) { setBookingError('Số điện thoại chưa đúng, quý khách vui lòng kiểm tra lại.'); return; }
    setBookingError('');

    var btn = form.querySelector('[type="submit"]');
    setButtonLoading(btn, true);
    send({
      formType: 'booking',
      name: name,
      phone: phone,
      pickup: widget ? val(widget, 'pickup') : '',
      dropoff: widget ? val(widget, 'dropoff') : '',
      pickup_time: widget ? val(widget, 'pickup_time') : '',
      source: currentSource(),
      _hp: val(form, '_hp'),
    })
      .then(function (res) {
        if (res && res.ok) {
          form.reset();
          if (widget) widget.reset();
          closeOverlay(bookingOverlay, function () {
            showResult('success', 'Đã nhận yêu cầu đặt xe!',
              'Tổng đài Xe Taxi Eakar sẽ gọi lại xác nhận chuyến đi trong ít phút. Cảm ơn quý khách!');
          });
        } else {
          setBookingError((res && res.error) || 'Có lỗi xảy ra, quý khách vui lòng thử lại.');
        }
      })
      .finally(function () {
        setButtonLoading(btn, false);
      });
  }

  // ------------------------------------------------------------ đăng ký tư vấn

  function wireContact(form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = val(form, 'full_name');
      var phone = val(form, 'phone_number');
      if (!name) { showResult('error', 'Thiếu thông tin', 'Quý khách vui lòng nhập họ và tên.'); return; }
      if (!isValidPhone(phone)) {
        showResult('error', 'Thiếu thông tin', 'Số điện thoại chưa đúng, quý khách vui lòng kiểm tra lại.');
        return;
      }
      var btn = form.querySelector('[type="submit"]');
      setButtonLoading(btn, true);
      send({
        formType: 'contact',
        name: name,
        phone: phone,
        address: val(form, 'address'),
        source: currentSource(),
        _hp: val(form, '_hp'),
      })
        .then(function (res) {
          if (res && res.ok) {
            form.reset();
            showResult('success', 'Đã gửi đăng ký!',
              'Cảm ơn quý khách. Xe Taxi Eakar sẽ gọi lại tư vấn trong thời gian sớm nhất.');
          } else {
            showResult('error', 'Gửi không thành công', (res && res.error) || 'Có lỗi xảy ra, quý khách vui lòng thử lại.');
          }
        })
        .finally(function () {
          setButtonLoading(btn, false);
        });
    });
  }

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (resultOverlay && !resultOverlay.hidden) closeResultModal();
    else if (bookingOverlay && !bookingOverlay.hidden) closeBookingModal();
  });

  function init() {
    var widget = document.getElementById('quickBookingForm');
    if (widget) {
      widget.addEventListener('submit', function (e) {
        e.preventDefault();
        openBookingModal(widget);
      });
    }
    Array.prototype.forEach.call(document.querySelectorAll('#dangkyForm'), wireContact);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
