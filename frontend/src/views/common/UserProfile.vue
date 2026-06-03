<template>
  <div class="user-profile-page">
    <section class="page-card">
      <div class="eyebrow">用户资料</div>
      <h2>用户 {{ userId }}</h2>
      <p>{{ profileHint }}</p>
      <div class="actions">
        <van-button plain type="warning" block :to="complaintRoute">投诉该用户</van-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

function getSessionRole() {
  try {
    return String(JSON.parse(localStorage.getItem('session') || '{}').role || '').toLowerCase()
  } catch {
    return ''
  }
}

const userId = computed(() => String(route.params.userId || ''))
const orderId = computed(() => String(route.query.orderId || ''))
const viewerRole = computed(() => String(route.query.viewer || '').toLowerCase())
const currentViewerRole = computed(() => viewerRole.value || getSessionRole())
const targetRole = computed(() => {
  const value = String(route.query.target || '').toLowerCase()
  if (value === 'driver') return 'driver'
  if (value === 'passenger') return 'passenger'
  return 'user'
})

const complaintRoute = computed(() => ({
  path: currentViewerRole.value === 'driver' ? '/driver/feedback' : '/passenger/feedback',
  query: {
    username: userId.value,
    orderId: orderId.value || undefined,
    target: targetRole.value,
  },
}))

const profileHint = computed(() => {
  if (orderId.value) {
    const targetName = targetRole.value === 'driver' ? '接单车主' : '同行乘客'
    return `这里用于查看 ${targetName} 的资料。如需聊天，请返回订单页面进入订单聊天。`
  }
  return '这里用于查看对方资料。如需联系，请从对应订单页面进入聊天。'
})
</script>

<style scoped>
.user-profile-page { display: grid; gap: 12px; }
.eyebrow { color: #165dff; font-size: 12px; font-weight: 700; margin-bottom: 4px; }
h2 { margin: 0 0 8px; color: #172033; }
p { margin: 0; color: #65758b; font-size: 13px; line-height: 1.6; }
.actions { display: grid; gap: 8px; margin-top: 16px; }
</style>
