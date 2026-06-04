/*
 * api-client.js — Client REST mỏng cho backend FastAPI (server/api.py).
 * Web (user + admin) gọi qua đây thay cho localStorage -> dùng chung db.json với agent.
 */
(function (global) {
  async function j(method, url, body) {
    const opt = { method, headers: {} };
    if (body !== undefined) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    const res = await fetch(url, opt);
    const data = await res.json().catch(() => null);
    if (!res.ok && res.status !== 409) throw new Error('HTTP ' + res.status);
    return { ok: res.ok, status: res.status, data };
  }

  global.API = {
    config: () => j('GET', '/api/config').then((r) => r.data),
    evaluate: (bookingCode, reasonCode, reasonText) =>
      j('POST', '/api/evaluate', { bookingCode, reasonCode, reasonText }).then((r) => r.data),
    listBookings: () => j('GET', '/api/bookings').then((r) => r.data.bookings),
    listRequests: () => j('GET', '/api/requests').then((r) => r.data.requests),
    getRequest: (id) => j('GET', '/api/requests/' + id).then((r) => r.data),
    createRequest: (bookingCode, reasonCode, reasonText) =>
      j('POST', '/api/requests', { bookingCode, reasonCode, reasonText }),
    approve: (id) => j('POST', '/api/requests/' + id + '/approve').then((r) => r.data),
    reject: (id, reason) => j('POST', '/api/requests/' + id + '/reject', { reason: reason || '' }).then((r) => r.data),
    reset: () => j('POST', '/api/requests/reset').then((r) => r.data),
    chat: (message, sessionId) => j('POST', '/api/agent/chat', { message, session_id: sessionId }).then((r) => r.data),
    resetChat: (sessionId) => j('POST', '/api/agent/reset', { session_id: sessionId }).then((r) => r.data),
  };

  global.money = (a, c) => Math.round(a || 0).toLocaleString('vi-VN') + ' ' + (c || 'VND');
})(window);
