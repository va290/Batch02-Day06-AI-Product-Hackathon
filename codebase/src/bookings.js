/* bookings.js — Trang "Phòng đã đặt": liệt kê booking, mỗi phòng → sang hủy/đổi điền sẵn mã. */
(function () {
  const POLICY = {
    free_cancellation: { label: 'Miễn phí hủy', tone: 'ok' },
    refundable: { label: 'Có thể hoàn (có phí)', tone: 'warn' },
    non_refundable: { label: 'Không hoàn tiền', tone: 'escalate' },
  };

  async function load() {
    const el = document.getElementById('bookings');
    let list;
    try { list = await API.listBookings(); }
    catch (e) { el.innerHTML = '<p class="empty">Mất kết nối backend.</p>'; return; }
    if (!list.length) { el.innerHTML = '<p class="empty">Chưa có phòng đã đặt.</p>'; return; }
    el.innerHTML = list.map((b) => {
      const p = POLICY[b.policyType] || { label: b.policyType, tone: 'ask' };
      return '<div class="req-row tone-' + p.tone + '">' +
        '<div class="req-top"><b>🏨 ' + b.hotel + '</b><span class="badge ' + p.tone + ' sm">' + p.label + '</span></div>' +
        '<div class="req-meta">' + b.room + ' · nhận phòng ' + b.checkIn + '</div>' +
        '<div class="req-meta">Mã ' + b.code + ' · ' + money(b.amount, b.currency) + '</div>' +
        '<div class="cta"><a class="btn primary sm" href="cancel.html?code=' + b.code + '">Hủy / Đổi phòng</a></div>' +
        '</div>';
    }).join('');
  }
  load();
})();
