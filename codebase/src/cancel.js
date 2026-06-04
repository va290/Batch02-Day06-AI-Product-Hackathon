/*
 * cancel.js — Trang "Hỗ trợ hủy/đổi". Gọi backend REST; điền sẵn mã từ ?code=.
 */
(function () {
  const $ = (s) => document.querySelector(s);
  let CONFIG = { reasonOptions: [], disclaimers: [], statusLabel: {} };
  const reasonSelect = $('#reason');
  const reasonTextWrap = $('#reason-text-wrap');
  const resultEl = $('#result');
  const STATUS_TONE = { auto_eligible: 'ok', eligible_with_fee: 'warn', needs_human: 'escalate', needs_clarification: 'ask', not_found: 'escalate' };

  async function init() {
    CONFIG = await API.config();
    const ph = document.createElement('option');
    ph.value = ''; ph.textContent = '— Chọn lý do —'; ph.disabled = true; ph.selected = true;
    reasonSelect.appendChild(ph);
    CONFIG.reasonOptions.forEach((r) => {
      const o = document.createElement('option'); o.value = r.code; o.textContent = r.label; reasonSelect.appendChild(o);
    });
    reasonSelect.addEventListener('change', () => {
      reasonTextWrap.style.display = reasonSelect.value === 'other' ? 'block' : 'none';
      clearError();
    });
    ['#booking-code', '#reason-text'].forEach((s) => $(s).addEventListener('input', clearError));
    document.querySelectorAll('[data-fill]').forEach((chip) =>
      chip.addEventListener('click', () => { $('#booking-code').value = chip.getAttribute('data-fill'); clearError(); }));
    const code = new URLSearchParams(location.search).get('code');
    if (code) $('#booking-code').value = code;
    $('#cancel-form').addEventListener('submit', onSubmit);
  }

  // ---- Validate input (không cho để trống) ----
  function showError(msg) { const e = $('#form-error'); e.textContent = msg; e.hidden = false; }
  function clearError() {
    const e = $('#form-error'); e.hidden = true; e.textContent = '';
    document.querySelectorAll('.field .invalid').forEach((x) => x.classList.remove('invalid'));
  }
  function fail(el, msg) { showError(msg); el.classList.add('invalid'); el.focus(); return false; }
  function validate() {
    clearError();
    if (!$('#booking-code').value.trim()) return fail($('#booking-code'), 'Vui lòng nhập mã đặt phòng.');
    if (!reasonSelect.value) return fail(reasonSelect, 'Vui lòng chọn lý do hủy/đổi.');
    if (reasonSelect.value === 'other' && !$('#reason-text').value.trim())
      return fail($('#reason-text'), 'Vui lòng mô tả lý do hủy/đổi.');
    return true;
  }

  const row = (k, v) => '<div class="kv-row"><span>' + k + '</span><b>' + v + '</b></div>';
  function feeBlock(d) {
    if (d.feePercent == null) return '';
    const cur = (d.booking && d.booking.currency) || 'VND';
    return '<div class="kv">' +
      (d.hotelFee != null ? row('Phí khách sạn', money(d.hotelFee, cur)) : '') +
      (d.procFee != null ? row('Phí xử lý Traveloka (10%, kẹp 32k–470k)', money(d.procFee, cur)) : '') +
      row('Tổng phí', money(d.feeAmount || 0, cur) + ' (~' + (d.feePercent || 0) + '%)') +
      (d.refundAmount != null ? row('Hoàn lại', money(d.refundAmount, cur)) : '') +
      (d.timelineText ? row('Thời gian hoàn', d.timelineText) : '') + '</div>';
  }
  const warningsBlock = (d) => (!d.warnings || !d.warnings.length) ? '' :
    '<ul class="warnings">' + d.warnings.map((w) => '<li>⚠️ ' + w + '</li>').join('') + '</ul>';
  const disclaimerBlock = () =>
    '<ul class="disclaimers">' + CONFIG.disclaimers.map((t) => '<li>ℹ️ ' + t + '</li>').join('') + '</ul>';
  const bookingBlock = (b) => !b ? '' :
    '<div class="booking-card"><div class="booking-hotel">🏨 ' + b.hotel + '</div>' +
    '<div class="booking-meta">' + b.room + ' · nhận phòng ' + b.checkIn + '</div>' +
    '<div class="booking-meta">Mã ' + b.code + ' · ' + money(b.amount, b.currency) + '</div></div>';
  function ctaBlock(d) {
    switch (d.recommendedAction) {
      case 'auto_cancel': return '<button class="btn primary" data-act="confirm">Xác nhận hủy (miễn phí)</button>';
      case 'confirm': return '<button class="btn primary" data-act="confirm">Đồng ý &amp; xác nhận hủy</button><button class="btn ghost" data-act="reset">Để sau</button>';
      case 'escalate': return '<button class="btn warn" data-act="escalate">Gửi yêu cầu &amp; chuyển hỗ trợ</button><button class="btn ghost" data-act="reset">Quay lại</button>';
      case 'clarify': return '<button class="btn primary" data-act="reset">Nhập lại lý do</button>';
      default: return '';
    }
  }
  const badgeText = (s) => ({ auto_eligible: 'HAPPY · Đủ điều kiện', eligible_with_fee: 'CÓ PHÍ · Cần xác nhận', needs_human: 'CHUYỂN NGƯỜI', needs_clarification: 'HỎI LẠI', not_found: 'KHÔNG TÌM THẤY' }[s] || s);

  function render(d) {
    const tone = STATUS_TONE[d.status] || 'ask';
    resultEl.innerHTML = '<div class="decision card tone-' + tone + '">' +
      '<div class="badge ' + tone + '">' + badgeText(d.status) + '</div>' +
      '<h2>' + d.headline + '</h2>' + bookingBlock(d.booking) +
      '<p class="detail">' + d.detail + '</p>' + feeBlock(d) + warningsBlock(d) +
      (d.policySource ? '<div class="policy">📑 Nguồn: ' + d.policySource + '</div>' : '') +
      '<div class="cta">' + ctaBlock(d) + '</div>' +
      '<div class="decided-by">Quyết định bởi: ' + d.decidedBy + '</div></div>';
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    resultEl.querySelectorAll('[data-act]').forEach((b) => b.addEventListener('click', () => handleAct(b.getAttribute('data-act'), d)));
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    const d = await API.evaluate($('#booking-code').value.trim(), reasonSelect.value, $('#reason-text').value.trim());
    render(d);
  }

  async function handleAct(act, d) {
    if (act === 'reset') return reset();
    const code = $('#booking-code').value;
    if (act === 'escalate' && d.status === 'not_found') return showHandoff(d, null);
    const res = await API.createRequest(code, reasonSelect.value, $('#reason-text').value);
    const rec = res.data && res.data.request;
    if (!rec) return reset();
    if (act === 'confirm') showSubmitted(rec); else showHandoff(d, rec);
  }

  const mineLink = '<a class="btn primary" href="requests.html">Xem "Yêu cầu của tôi"</a>';
  function showSubmitted(rec) {
    const isAuto = rec.status === 'auto_approved';
    resultEl.innerHTML = '<div class="decision card tone-ok">' +
      '<div class="badge ok">' + (isAuto ? 'ĐÃ DUYỆT' : 'ĐÃ GỬI YÊU CẦU') + '</div>' +
      '<h2>' + (isAuto ? 'Hủy miễn phí đã được duyệt ✅' : 'Đã gửi yêu cầu hủy ✅') + '</h2>' +
      '<p class="detail">Mã yêu cầu <b>' + rec.id + '</b> cho đặt phòng ' + rec.bookingCode + '. ' +
      (isAuto ? 'Hoàn ' + money(rec.refundAmount, rec.currency) + ' ' + (rec.timelineText || '') + '.'
              : 'Đang chờ bộ phận hỗ trợ duyệt.') + '</p>' +
      disclaimerBlock() +
      '<div class="cta">' + mineLink + '<button class="btn ghost" data-act="reset">Về đầu</button></div></div>';
    bindReset();
  }
  function showHandoff(d, rec) {
    resultEl.innerHTML = '<div class="decision card tone-escalate">' +
      '<div class="badge escalate">' + (rec ? 'ĐÃ GỬI · CHỜ DUYỆT' : 'ĐANG CHUYỂN HỖ TRỢ') + '</div>' +
      '<h2>Đã chuyển hỗ trợ kèm ngữ cảnh 👤</h2>' +
      (rec ? '<p class="detail">Mã yêu cầu <b>' + rec.id + '</b> · đơn vị lưu trú sẽ xét.</p>' : '') +
      '<p class="detail">Nhân viên nhận TOÀN BỘ thông tin dưới đây — bạn không phải kể lại từ đầu:</p>' +
      '<div class="handoff">' +
      '<div>• Mã đặt phòng: <b>' + ($('#booking-code').value || '(trống)') + '</b></div>' +
      '<div>• Lý do: <b>' + currentReasonLabel() + '</b></div>' +
      (d.booking ? '<div>• Booking: <b>' + d.booking.hotel + ' (' + d.booking.code + ')</b></div>' : '') +
      '<div>• Kết luận hệ thống: <b>' + d.headline + '</b></div>' +
      (d.policySource ? '<div>• Chính sách liên quan: ' + d.policySource + '</div>' : '') + '</div>' +
      (rec ? disclaimerBlock() : '') +
      '<div class="cta">' + (rec ? mineLink : '') + '<button class="btn ghost" data-act="reset">Về đầu</button></div></div>';
    bindReset();
  }
  function bindReset() { const r = resultEl.querySelector('[data-act=reset]'); if (r) r.addEventListener('click', reset); }
  function currentReasonLabel() {
    if (reasonSelect.value === 'other') return ($('#reason-text').value || '').trim() || 'Lý do khác';
    const f = CONFIG.reasonOptions.find((r) => r.code === reasonSelect.value);
    return f ? f.label : reasonSelect.value;
  }
  function reset() { resultEl.innerHTML = ''; }

  init();
})();
