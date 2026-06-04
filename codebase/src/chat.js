/*
 * chat.js — Chatbot AI nổi, dùng chung cho mọi trang khách hàng.
 * Yêu cầu trang có sẵn markup #chat-fab / #chat-panel / #chat-log / #chat-form.
 */
(function () {
  const $ = (s) => document.querySelector(s);
  if (!$('#chat-fab') || !$('#chat-panel')) return; // trang không có chatbot

  function sessionId() {
    let sid = localStorage.getItem('tvl_chat_sid');
    if (!sid) { sid = 'sid-' + Date.now() + '-' + Math.floor(Math.random() * 1e6); localStorage.setItem('tvl_chat_sid', sid); }
    return sid;
  }
  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  // Render an toàn: escape trước, rồi cho phép **đậm** + tự tạo link tới request.html cho mã REQ-xxxx.
  function renderRich(text) {
    let s = escapeHtml(text);
    s = s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
    s = s.replace(/\b(REQ-\d+)\b/g, '<a href="request.html?id=$1" target="_blank" rel="noopener">$1</a>');
    return s.replace(/\n/g, '<br>');
  }
  function appendChat(role, html) {
    const log = $('#chat-log');
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.innerHTML = html;
    log.appendChild(div); log.scrollTop = log.scrollHeight;
  }

  async function onChat(e) {
    e.preventDefault();
    const input = $('#chat-input');
    const msg = input.value.trim(); if (!msg) return;
    appendChat('user', escapeHtml(msg)); input.value = ''; input.disabled = true;
    appendChat('ai', '<i>đang xử lý…</i>');
    const log = $('#chat-log');
    try {
      const out = await API.chat(msg, sessionId());
      log.lastChild.remove();
      appendChat('ai', renderRich(out.reply || '(không có phản hồi)'));
      if (out.trace && out.trace.length)
        appendChat('ai', '<span class="trace">⚙ tool: ' + out.trace.map((t) => escapeHtml(t.tool)).join(' → ') + '</span>');
      if (typeof window.refreshData === 'function') window.refreshData(); // cập nhật list nếu đang ở trang đó
    } catch (err) {
      log.lastChild.remove(); appendChat('ai', '(lỗi kết nối agent)');
    } finally { input.disabled = false; input.focus(); }
  }

  const fab = $('#chat-fab'), panel = $('#chat-panel');
  fab.addEventListener('click', () => { panel.hidden = false; fab.classList.add('hidden'); $('#chat-input').focus(); });
  $('#chat-close').addEventListener('click', () => { panel.hidden = true; fab.classList.remove('hidden'); });
  $('#chat-form').addEventListener('submit', onChat);
  $('#chat-reset').addEventListener('click', async () => {
    try { await API.resetChat(sessionId()); } catch (e) {}
    localStorage.removeItem('tvl_chat_sid');
    $('#chat-log').innerHTML = '';
  });
})();
