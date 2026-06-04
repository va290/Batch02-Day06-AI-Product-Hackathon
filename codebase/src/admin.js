/*
 * admin.js — Trang Support/Admin. Gọi backend REST; duyệt/từ chối yêu cầu.
 * Dùng chung DB với trang user và AI agent. Polling để tự cập nhật.
 */
(function () {
  const $ = (s) => document.querySelector(s);
  let CONFIG = { statusLabel: {} };

  const REQ_TONE = { pending: 'warn', approved: 'ok', rejected: 'escalate', auto_approved: 'ok' };
  const TYPE_LABEL = {
    free: 'Miễn phí hủy', fee: 'Có phí', non_refundable: 'Không hoàn (đơn vị lưu trú xét)', force_majeure: 'Bất khả kháng',
  };

  function feeLine(r) {
    if (r.feeAmount == null && r.refundAmount == null) return '';
    return '<div class="req-meta">' +
      (r.feeAmount != null ? 'Phí: ' + money(r.feeAmount, r.currency) + ' · ' : '') +
      (r.refundAmount != null ? 'Hoàn dự kiến: ' + money(r.refundAmount, r.currency) : '') + '</div>';
  }
  function actions(r) {
    if (r.status !== 'pending')
      return '<div class="req-meta resolved">Đã xử lý ' + (r.decidedAt || '') +
        (r.rejectReason ? ' · Lý do từ chối: ' + r.rejectReason : '') + '</div>';
    return '<div class="cta">' +
      '<button class="btn primary sm" data-approve="' + r.id + '">Duyệt hoàn tiền</button>' +
      '<button class="btn warn sm" data-reject="' + r.id + '">Từ chối</button></div>';
  }
  const stat = (label, n, tone) =>
    '<div class="stat tone-' + tone + '"><div class="stat-n">' + n + '</div><div class="stat-l">' + label + '</div></div>';

  async function render() {
    let list;
    try { list = await API.listRequests(); } catch (e) { $('#queue').innerHTML = '<p class="empty">Mất kết nối backend.</p>'; return; }
    const pending = list.filter((r) => r.status === 'pending').length;
    const approved = list.filter((r) => r.status === 'approved' || r.status === 'auto_approved').length;
    const rejected = list.filter((r) => r.status === 'rejected').length;
    $('#stats').innerHTML = stat('Chờ duyệt', pending, 'warn') + stat('Đã duyệt', approved, 'ok') + stat('Từ chối', rejected, 'escalate');

    $('#queue').innerHTML = list.map((r) => {
      const tone = REQ_TONE[r.status] || 'ask';
      return '<div class="card req-admin tone-' + tone + '">' +
        '<div class="req-top"><b>' + r.id + '</b> · ' + r.hotel +
        '<span class="badge ' + tone + ' sm">' + (CONFIG.statusLabel[r.status] || r.status) + '</span></div>' +
        '<div class="req-meta">Mã ' + r.bookingCode + ' · ' + r.room + ' · ' + money(r.amount, r.currency) + '</div>' +
        '<div class="req-meta">Loại: ' + (TYPE_LABEL[r.type] || r.type) + ' · Lý do: ' + r.reasonLabel + ' · gửi ' + r.createdAt + '</div>' +
        feeLine(r) + (r.policySource ? '<div class="policy">📑 ' + r.policySource + '</div>' : '') + actions(r) + '</div>';
    }).join('');

    document.querySelectorAll('[data-approve]').forEach((b) =>
      b.addEventListener('click', async () => { await API.approve(b.getAttribute('data-approve')); render(); }));
    document.querySelectorAll('[data-reject]').forEach((b) =>
      b.addEventListener('click', async () => {
        const reason = window.prompt('Lý do từ chối (gửi cho khách hàng):', 'Không đủ điều kiện theo chính sách hủy của đơn vị lưu trú.');
        if (reason === null) return;
        await API.reject(b.getAttribute('data-reject'), reason.trim()); render();
      }));
  }

  async function init() {
    CONFIG = await API.config();
    $('#reset-demo').addEventListener('click', async () => {
      if (window.confirm('Xoá toàn bộ yêu cầu và nạp lại dữ liệu mẫu?')) { await API.reset(); render(); }
    });
    await render();
    setInterval(render, 3500);
  }
  init();
})();
