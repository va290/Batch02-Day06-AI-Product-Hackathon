/* request-detail.js — Trang chi tiết 1 yêu cầu hoàn/hủy (preview qua URL ?id=REQ-xxxx). */
(function () {
  const TONE = { pending: 'warn', approved: 'ok', rejected: 'escalate', auto_approved: 'ok' };
  const LABEL = {
    pending: 'Chờ duyệt', approved: 'Đã duyệt — đang hoàn tiền',
    rejected: 'Bị từ chối', auto_approved: 'Đã duyệt (tự động, miễn phí)',
  };
  const TYPE = { free: 'Miễn phí hủy', fee: 'Có phí', non_refundable: 'Không hoàn (đơn vị lưu trú xét)', force_majeure: 'Bất khả kháng' };
  const row = (k, v) => v == null || v === '' ? '' : '<div class="kv-row"><span>' + k + '</span><b>' + v + '</b></div>';

  async function load() {
    const id = new URLSearchParams(location.search).get('id');
    const el = document.getElementById('detail');
    if (!id) { el.innerHTML = '<p class="empty">Thiếu mã yêu cầu (?id=REQ-...).</p>'; return; }
    let r;
    try { r = await API.getRequest(id); }
    catch (e) { el.innerHTML = '<p class="empty">Không tìm thấy yêu cầu <b>' + id + '</b>.</p>'; return; }
    const tone = TONE[r.status] || 'ask';
    el.innerHTML =
      '<div class="decision card tone-' + tone + '">' +
      '<div class="badge ' + tone + '">' + (LABEL[r.status] || r.status) + '</div>' +
      '<h2>' + r.id + ' · ' + r.hotel + '</h2>' +
      '<div class="booking-card"><div class="booking-meta">' + r.room + '</div>' +
      '<div class="booking-meta">Mã đặt phòng ' + r.bookingCode + ' · ' + money(r.amount, r.currency) + '</div></div>' +
      '<div class="kv">' +
      row('Loại', TYPE[r.type] || r.type) +
      row('Lý do', r.reasonLabel) +
      row('Phí', r.feeAmount != null ? money(r.feeAmount, r.currency) : null) +
      row('Hoàn lại', r.refundAmount != null ? money(r.refundAmount, r.currency) : null) +
      row('Thời gian hoàn', r.timelineText) +
      row('Ngày gửi', r.createdAt) +
      row('Ngày xử lý', r.decidedAt) +
      row('Lý do từ chối', r.rejectReason) +
      '</div>' +
      (r.policySource ? '<div class="policy">📑 Nguồn: ' + r.policySource + '</div>' : '') +
      '</div>';
  }
  load();
})();
