const profileCache = new Map()
const pendingRequests = new Map()

function normalizeUserId(userId) {
  return String(userId ?? '').trim()
}

function fallbackUsername(userId) {
  const id = normalizeUserId(userId)
  return id || '未知用户'
}

function isNumericUserId(userId) {
  return /^\d+$/.test(normalizeUserId(userId))
}

function normalizeProfile(userId, payload = {}) {
  const id = normalizeUserId(payload.userId ?? payload.id ?? userId)
  return {
    userId: id,
    username: String(payload.username || fallbackUsername(id)),
  }
}

export function getCachedUsername(userId) {
  const id = normalizeUserId(userId)
  return profileCache.get(id)?.username || fallbackUsername(id)
}

export async function fetchUserProfile(userId) {
  const id = normalizeUserId(userId)
  if (!id) return normalizeProfile(id)
  if (profileCache.has(id)) return profileCache.get(id)
  if (pendingRequests.has(id)) return pendingRequests.get(id)

  if (!isNumericUserId(id)) {
    const fallback = normalizeProfile(id)
    profileCache.set(id, fallback)
    return fallback
  }

  const request = fetch(`/api/users/profile/${encodeURIComponent(id)}`)
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    })
    .then((data) => normalizeProfile(id, data))
    .catch(() => normalizeProfile(id))
    .then((profile) => {
      profileCache.set(id, profile)
      pendingRequests.delete(id)
      return profile
    })

  pendingRequests.set(id, request)
  return request
}

export async function fetchUserProfiles(userIds) {
  const ids = Array.from(new Set((userIds || []).map(normalizeUserId).filter(Boolean)))
  const profiles = await Promise.all(ids.map((id) => fetchUserProfile(id)))
  return profiles.reduce((map, profile) => {
    map[profile.userId] = profile
    return map
  }, {})
}
