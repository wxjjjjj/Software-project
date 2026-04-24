function buildErrorMessage(payload, fallback) {
  // 统一后端不同错误结构，抽取可读提示。
  if (!payload) return fallback
  if (typeof payload === 'string') return payload
  if (payload.detail) return String(payload.detail)
  if (payload.message) return String(payload.message)
  return fallback
}

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

function getUserId() {
  const session = getSession()
  return String(session.userId || session.username || 'dev-user-1')
}

function buildHeaders(isJson = true) {
  const session = getSession()
  const headers = {
    'X-User-Id': getUserId()
  }
  if (session.role === 'admin') {
    headers['X-User-Role'] = 'admin'
  }
  if (isJson) {
    headers['Content-Type'] = 'application/json'
  }
  return headers
}

async function request(url, options = {}) {
  // 车辆相关接口通用请求封装。
  const response = await fetch(url, options)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = buildErrorMessage(payload, '请求失败，请稍后重试')
    throw new Error(message)
  }
  return payload
}

export function fetchOwnerVehicles() {
  // 查询当前登录车主的车辆列表。
  return request('/api/vehicles', {
    method: 'GET',
    headers: buildHeaders(false)
  })
}

export function createOwnerVehicle(payload) {
  // 新增车辆。
  return request('/api/vehicles', {
    method: 'POST',
    headers: buildHeaders(true),
    body: JSON.stringify(payload)
  })
}

export function updateOwnerVehicle(vehicleId, payload) {
  // 编辑车辆基础信息。
  return request(`/api/vehicles/${vehicleId}`, {
    method: 'PUT',
    headers: buildHeaders(true),
    body: JSON.stringify(payload)
  })
}

export function updateOwnerVehicleStatus(vehicleId, status) {
  // 更新车辆状态（available/disabled）。
  return request(`/api/vehicles/${vehicleId}/status`, {
    method: 'PATCH',
    headers: buildHeaders(true),
    body: JSON.stringify({ status })
  })
}

export function deleteOwnerVehicle(vehicleId) {
  // 按车辆 id 删除记录。
  return request(`/api/vehicles/${vehicleId}`, {
    method: 'DELETE',
    headers: buildHeaders(false)
  })
}

export function updateAdminVehicleVerified(vehicleId, verified) {
  // 管理员修改车辆认证状态。
  return request(`/api/vehicles/${vehicleId}/verified`, {
    method: 'PATCH',
    headers: buildHeaders(true),
    body: JSON.stringify({ verified })
  })
}

export function submitVehicleVerifyRequest(vehicleId, payload) {
  // 车主提交车辆认证资料。
  return request(`/api/vehicles/${vehicleId}/verify-request`, {
    method: 'POST',
    headers: buildHeaders(true),
    body: JSON.stringify(payload)
  })
}

export function fetchVehicleVerifyRequests(status = 'pending') {
  // 管理员获取车辆认证申请列表。
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request(`/api/vehicles/verify-requests${query}`, {
    method: 'GET',
    headers: buildHeaders(false)
  })
}

export function reviewVehicleVerifyRequest(requestId, decision, review_note = '') {
  // 管理员审核车辆认证资料。
  return request(`/api/vehicles/verify-requests/${requestId}/review`, {
    method: 'PATCH',
    headers: buildHeaders(true),
    body: JSON.stringify({ decision, review_note })
  })
}
