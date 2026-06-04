/* requests.js — Trang "Yêu cầu của tôi": danh sách + trạng thái, tự cập nhật (polling). */
(function () {
  let STATUS_LABEL = {};
  const TONE = { pending: 'warn', approved: 'ok', rejected: 'escalate', auto_approved: 'ok' };

  function detail(r) {
    if (r.status === 'approved') return 'Đã duyệt — hoàn ' + money(r.refundAmount, r.currency) + ' ' + (r.timelineText || '') + '.';
    if (r.status === 'auto_approved') return 'Miễn phí — hoàn ' + money(r.refundAmount, r.currency) + ' ' + (r.timelineText || '') + '.';
    if (r.status === 'rejected') return 'Bị từ chối — ' + (r.rejectReason || '');
    return 'Đang chờ bộ phận hỗ trợ / đơn vị lưu trú duyệt.';
  }

  async function render() {
    const el = document.getElementById('my-requests');
    let list;
    try { list = await API.listRequests(); }
    catch (e) { el.innerHTML = '<p class="empty">Mất kết nối backend.</p>'; return; }
    if (!list.length) { el.innerHTML = '<p class="empty">Chưa có yêu cầu nào.</p>'; return; }
    el.innerHTML = list.map((r) => {
      const tone = TONE[r.status] || 'ask';
      return '<div class="req-row tone-' + tone + '">' +
        '<div class="req-top"><b><a href="request.html?id=' + r.id + '">' + r.id + '</a></b> · ' + r.hotel +
        '<span class="badge ' + tone + ' sm">' + (STATUS_LABEL[r.status] || r.status) + '</span></div>' +
        '<div class="req-meta">Mã ' + r.bookingCode + ' · ' + r.reasonLabel + ' · gửi ' + r.createdAt + '</div>' +
        '<div class="req-detail">' + detail(r) + '</div></div>';
    }).join('');
  }

  window.refreshData = render; // để chatbot gọi cập nhật ngay sau khi tạo yêu cầu

  (async function init() {
    try { STATUS_LABEL = (await API.config()).statusLabel || {}; } catch (e) {}
    await render();
    setInterval(render, 3500);
  })();
})();
