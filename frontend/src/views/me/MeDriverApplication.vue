<template>
  <div class="driver-apply-page">
    <section class="page-card">
      <h2>申请成为车主</h2>
      <p class="hint">这里承接 wyx 账号域的车主身份申请。通过后可切换车主模式；车辆登记与车辆认证在“我的车辆”中完成。</p>

      <div class="status-box">
        <span>当前状态</span>
        <van-tag :type="statusType">{{ statusText }}</van-tag>
      </div>

      <van-button type="primary" block :loading="loading" @click="submitApplication">
        {{ status === 'pending' ? '已提交，刷新状态' : '提交车主身份申请' }}
      </van-button>
      <van-button plain type="default" block to="/me/vehicles">
        去登记车辆
      </van-button>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { showNotify } from 'vant'

const loading = ref(false)
const status = ref('unapplied')

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

const statusText = computed(() => ({
  unapplied: '未申请',
  pending: '审核中',
  approved: '已通过',
  active: '已通过',
  banned: '已停用'
})[status.value] || status.value)

const statusType = computed(() => {
  if (status.value === 'approved' || status.value === 'active') return 'success'
  if (status.value === 'pending') return 'warning'
  if (status.value === 'banned') return 'danger'
  return 'default'
})

async function loadProfile() {
  const session = getSession()
  if (!session.userId) return
  try {
    const res = await fetch(`/api/users/profile/${session.userId}`)
    if (!res.ok) return
    const data = await res.json()
    status.value = data.driver_status || 'unapplied'
    if (['approved', 'active'].includes(status.value)) {
      session.ownerVerified = true
      localStorage.setItem('session', JSON.stringify(session))
    }
  } catch {
    status.value = session.ownerVerified ? 'approved' : 'unapplied'
  }
}

async function submitApplication() {
  const session = getSession()
  if (!session.userId) {
    showNotify({ type: 'warning', message: '请先登录' })
    return
  }
  loading.value = true
  try {
    const res = await fetch(`/api/users/driver/apply/${session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        license_plate: '待登记',
        car_model: '待登记',
        car_color: '待登记'
      })
    })
    if (!res.ok) throw new Error('申请提交失败')
    status.value = 'pending'
    showNotify({ type: 'success', message: '车主身份申请已提交' })
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '申请失败' })
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.driver-apply-page { display: grid; gap: 12px; }
h2 { margin: 0 0 8px; color: #172033; }
.hint { color: #65758b; font-size: 13px; line-height: 1.6; margin: 0 0 14px; }
.status-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 12px;
  background: #f6f8fb;
  margin-bottom: 12px;
}
:deep(.van-button) { margin-top: 8px; }
</style>
