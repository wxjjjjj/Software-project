/**
 * 订单域前端 API 封装
 * 负责人：hws
 * 所有接口经过网关 8000 → ride 服务 8002
 */

/** 从 localStorage 取当前用户 ID */
function getUserId() {
  try {
    const s = JSON.parse(localStorage.getItem('session') || '{}')
    // 优先用 userId，若 account 域还未设置则用 username，再兜底开发用值
    return s.userId || s.username || 'dev-user-1'
  } catch {
    return 'dev-user-1'
  }
}

function buildErrorMessage(payload, fallback) {
  if (!payload) return fallback
  if (typeof payload === 'string') return payload
  if (payload.detail) return String(payload.detail)
  if (payload.message) return String(payload.message)
  return fallback
}

function buildHeaders() {
  const s = JSON.parse(localStorage.getItem('session') || '{}')
  const headers = {
    'Content-Type': 'application/json',
    'X-User-Id': getUserId(),
  }
  if (s.role === 'admin') headers['X-User-Role'] = 'admin'
  return headers
}

async function req(method, path, body = null) {
  const opts = { method, headers: buildHeaders() }
  if (body !== null) opts.body = JSON.stringify(body)
  const res = await fetch(`/api${path}`, opts)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(buildErrorMessage(data, `HTTP ${res.status}`))
  return data
}

// ── 订单接口 ──────────────────────────────────────────────────────────────────

export const rideApi = {
  /** 1. 发布订单 */
  publishOrder(payload) {
    return req('POST', '/orders', payload)
  },

  /** 2. 搜索订单（支持标签筛选） */
  searchOrders({ start_loc, end_loc, time_from, time_to, tags } = {}) {
    const q = new URLSearchParams()
    if (start_loc) q.set('start_loc', start_loc)
    if (end_loc)   q.set('end_loc', end_loc)
    if (time_from) q.set('time_from', time_from)
    if (time_to)   q.set('time_to', time_to)
    if (tags?.length) q.set('tags', tags.join(','))
    const qs = q.toString()
    return req('GET', `/orders/search${qs ? '?' + qs : ''}`)
  },

  /** 3. 我的订单（乘客视角：发布+参与） */
  listMyOrders() {
    return req('GET', `/orders?passenger_id=${getUserId()}`)
  },

  /** 3. 车主已接订单 */
  listDriverOrders() {
    return req('GET', `/orders?owner_id=${getUserId()}`)
  },

  /** 3. 所有订单（管理员用） */
  listAllOrders() {
    return req('GET', '/orders')
  },

  /** 4. 订单详情 */
  getOrderDetail(orderId) {
    return req('GET', `/orders/${orderId}`)
  },

  /** 5. 修改订单 */
  updateOrder(orderId, payload) {
    return req('PUT', `/orders/${orderId}`, payload)
  },

  /** 6. 取消订单 */
  cancelOrder(orderId) {
    return req('POST', `/orders/${orderId}/cancel`)
  },

  /** 7. 加入订单 */
  joinOrder(orderId) {
    return req('POST', `/orders/${orderId}/join`)
  },

  /** 8. 车主接单 */
  acceptOrder(orderId, vehicleId) {
    return req('POST', `/orders/${orderId}/accept`, { vehicle_id: vehicleId })
  },

  /** 9. 标记完成（域3调用） */
  completeOrder(orderId) {
    return req('POST', `/orders/${orderId}/complete`, { operator: 'domain3' })
  },

  /** 10. 查询当前车主的车辆列表 */
  listMyVehicles() {
    return req('GET', '/vehicles')
  },
}

// ── 车辆接口 ──────────────────────────────────────────────────────────────────

export function fetchOwnerVehicles() {
  return req('GET', '/vehicles')
}

export function createOwnerVehicle(payload) {
  return req('POST', '/vehicles', payload)
}

export function updateOwnerVehicle(vehicleId, payload) {
  return req('PUT', `/vehicles/${vehicleId}`, payload)
}

export function updateOwnerVehicleStatus(vehicleId, status) {
  return req('PATCH', `/vehicles/${vehicleId}/status`, { status })
}

export function deleteOwnerVehicle(vehicleId) {
  return req('DELETE', `/vehicles/${vehicleId}`)
}

export function updateAdminVehicleVerified(vehicleId, verified) {
  return req('PATCH', `/vehicles/${vehicleId}/verified`, { verified })
}

export function submitVehicleVerifyRequest(vehicleId, payload) {
  return req('POST', `/vehicles/${vehicleId}/verify-request`, payload)
}

export function fetchVehicleVerifyRequests(status = 'pending') {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return req('GET', `/vehicles/verify-requests${query}`)
}

export function reviewVehicleVerifyRequest(requestId, decision, review_note = '') {
  return req('PATCH', `/vehicles/verify-requests/${requestId}/review`, {
    decision,
    review_note,
  })
}

// ── 工具函数 ──────────────────────────────────────────────────────────────────

/** 订单状态映射 */
export const STATUS_MAP = {
  published: { label: '招募中', type: 'success' },
  full:      { label: '已满员', type: 'warning' },
  locked:    { label: '已锁单', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'default' },
}

/** 可选标签列表 */
export const AVAILABLE_TAGS = ['宠物友好', '静音', '禁烟', '女性专属', '不绕路', '准时出发', '早高峰', '顺路']

/** 常用出行地点（用于输入建议） */
export const LOCATION_SUGGESTIONS = [
  // 学校/校区
  '软件园校区', '大学城', '南校区', '北校区', '东校区',
  // 交通枢纽
  '广州南站', '广州东站', '广州火车站', '天河客运站', '白云机场', '新白云机场T2',
  // 常用地点
  '天河区', '珠江新城', '体育西路', '岗顶', '华南理工大学',
  '南门', '北门', '东门', '西门', '正门',
  '地铁口', '公交站',
  // 本地区域（可根据实际校区修改）
  '学生宿舍', '教学楼', '图书馆', '食堂', '操场',
]

/** 估算每人均价 */
export function calcPerPersonPrice(totalPrice, groupSize, extraSeats) {
  const total = Number(totalPrice) || 0
  const seats = (Number(groupSize) || 1) + (Number(extraSeats) || 0)
  if (total <= 0 || seats <= 0) return null
  return (total / seats).toFixed(1)
}

/** 格式化出发时间显示 */
export function formatTime(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  const mo = d.getMonth() + 1
  const da = d.getDate()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${mo}月${da}日 ${hh}:${mm}`
}

/** 获取当前登录用户 ID（供页面组件使用） */
export { getUserId }

// ── 高德地图工具 ──────────────────────────────────────────────────────────────

const AMAP_KEY = 'a94c6fe44b146be2c229894626f0debf'

export async function searchPlaces(keyword, city = '广州') {
  if (!keyword?.trim()) return []
  const url = `/amap/v3/place/text?key=${AMAP_KEY}&keywords=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}&offset=8&output=JSON`
  try {
    const res = await fetch(url)
    const data = await res.json()
    if (data.status !== '1' || !data.pois?.length) return []
    return data.pois.map(p => ({ name: p.name, location: p.location }))
  } catch {
    return []
  }
}

export async function calcDrivingRoute(originLoc, destLoc) {
  if (!originLoc || !destLoc) return null
  const url = `/amap/v3/direction/driving?key=${AMAP_KEY}&origin=${originLoc}&destination=${destLoc}&output=JSON`
  try {
    const res = await fetch(url)
    const data = await res.json()
    if (data.status !== '1') return null
    const route = data.route.paths[0]
    const distance_m = Number(route.distance)
    const duration_s = Number(route.duration)
    const km = distance_m / 1000
    // 上海出租车计费：起步价 16元/3km，超出 3.1元/km
    const recommend_price = km <= 3 ? 16 : Math.round(16 + (km - 3) * 3.1)
    return { distance_m, duration_s, recommend_price }
  } catch {
    return null
  }
}
