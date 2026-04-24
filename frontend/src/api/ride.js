function buildErrorMessage(payload, fallback) {
  // 统一后端不同错误结构，抽取可读提示。
  if (!payload) return fallback
  if (typeof payload === 'string') return payload
  if (payload.detail) return String(payload.detail)
  if (payload.message) return String(payload.message)
  return fallback
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

export function fetchOwnerVehicles(ownerUserId) {
  // 查询指定车主的车辆列表。
  return request(`/api/vehicles?ownerUserId=${encodeURIComponent(ownerUserId)}`)
}

export function createOwnerVehicle(payload) {
  // 新增车辆。
  return request('/api/vehicles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export function updateOwnerVehicle(vehicleId, payload) {
  // 编辑车辆基础信息。
  return request(`/api/vehicles/${vehicleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export function updateOwnerVehicleStatus(vehicleId, status) {
  // 更新车辆状态（available/disabled）。
  return request(`/api/vehicles/${vehicleId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })
}

export function deleteOwnerVehicle(vehicleId) {
  // 按车辆 id 删除记录。
  return request(`/api/vehicles/${vehicleId}`, {
    method: 'DELETE'
  })
}
