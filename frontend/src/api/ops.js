// 交易运营域 API 封装
const BASE = '/api'

function getSession() {
  try { return JSON.parse(localStorage.getItem('session') || '{}') }
  catch { return {} }
}

function getUserId() {
  const s = getSession()
  if (s.userId) return Number(s.userId)
  if (s.role === 'admin') return 999
  return s.ownerVerified ? 2 : 1
}

async function request(url, method, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getSession().token
  if (token) headers['Authorization'] = `Bearer ${token}`
  const opts = { method, headers }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(url, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    // 处理 detail 可能是数组（Pydantic 校验错误）或对象的情况
    let message = '请求失败'
    if (err.detail) {
      if (typeof err.detail === 'string') {
        message = err.detail
      } else if (Array.isArray(err.detail) && err.detail.length > 0) {
        message = err.detail.map(e => e.msg || JSON.stringify(e)).join('; ')
      } else {
        message = JSON.stringify(err.detail)
      }
    } else {
      message = `HTTP ${res.status}`
    }
    throw new Error(message)
  }
  return res.json()
}

export function payOrder(orderId, payload) {
  return request(`${BASE}/payments/orders/${orderId}/pay`, 'POST', payload)
}

export function walletInfo(userId) {
  return request(`${BASE}/wallet/info?user_id=${userId}`, 'GET')
}

export function walletWithdraw(payload) {
  return request(`${BASE}/wallet/withdraw`, 'POST', payload)
}

export function walletLogs(userId, page = 1, size = 20) {
  return request(`${BASE}/wallet/logs?user_id=${userId}&page=${page}&size=${size}`, 'GET')
}

export function sendMessage(payload) {
  return request(`${BASE}/chat/messages`, 'POST', payload)
}

export function getMessages(orderId, userId) {
  return request(`${BASE}/chat/messages?order_id=${orderId}&user_id=${userId}`, 'GET')
}

export function markMessagesRead(orderId, userId) {
  return request(`${BASE}/chat/messages/read?order_id=${orderId}&user_id=${userId}`, 'PUT')
}

export function createComplaint(payload) {
  return request(`${BASE}/complaints`, 'POST', payload)
}

export function listComplaints(userId, page = 1, size = 20) {
  return request(`${BASE}/complaints?user_id=${userId}&page=${page}&size=${size}`, 'GET')
}

export function adminListComplaints(status, page = 1, size = 20) {
  let url = `${BASE}/admin/complaints?page=${page}&size=${size}`
  if (status !== undefined && status !== null) url += `&status=${status}`
  return request(url, 'GET')
}

export function adminHandleComplaint(ticketId, payload) {
  return request(`${BASE}/admin/complaints/${ticketId}`, 'PUT', payload)
}

export function adminStatistics() {
  return request(`${BASE}/admin/stats`, 'GET')
}

export function adminListWithdrawals(page = 1, size = 20) {
  return request(`${BASE}/admin/withdrawals?page=${page}&size=${size}`, 'GET')
}

export function adminApproveWithdrawal(userId) {
  return request(`${BASE}/admin/withdrawals/${userId}/approve`, 'POST')
}

export function adminRejectWithdrawal(userId) {
  return request(`${BASE}/admin/withdrawals/${userId}/reject`, 'POST')
}

export { getUserId }
