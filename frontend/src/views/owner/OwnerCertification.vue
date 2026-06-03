<template>
  <div class="driver-cert-page">
    <section class="page-card hero-card">
      <div class="eyebrow">Owner Verification</div>
      <h2>车主认证中心</h2>
      <p class="page-hint">先提交车主个人资质，管理员通过后，再新增车辆并进入车辆认证审核。</p>

      <div class="flow-card">
        <div class="flow-step" :class="{ active: status === 'unapplied', done: isApplied }">
          <span>1</span>
          <b>个人资质</b>
        </div>
        <div class="flow-line"></div>
        <div class="flow-step" :class="{ active: isApproved }">
          <span>2</span>
          <b>新增车辆</b>
        </div>
        <div class="flow-line"></div>
        <div class="flow-step" :class="{ active: isApproved }">
          <span>3</span>
          <b>车辆审核</b>
        </div>
      </div>
    </section>

    <section v-if="loadingProfile" class="page-card state-card">
      <van-loading type="spinner" color="#165DFF">正在同步账号状态...</van-loading>
    </section>

    <section v-else-if="status === 'unapplied'" class="page-card form-card">
      <h3>提交车主个人资质</h3>
      <p class="hint">请填写真实身份与驾驶证信息。通过后才会开放车辆登记和接单能力。</p>

      <div class="form-item">
        <label>真实姓名</label>
        <input v-model.trim="form.real_name" placeholder="请输入真实姓名" />
      </div>

      <div class="form-item">
        <label>身份证号</label>
        <input v-model.trim="form.id_card" placeholder="请输入身份证号" />
      </div>

      <div class="form-item">
        <label>驾驶证号</label>
        <input v-model.trim="form.driver_license_no" placeholder="请输入驾驶证号" />
      </div>

      <div class="form-item">
        <label>联系电话</label>
        <input v-model.trim="form.contact_phone" placeholder="用于管理员审核联系，可选" />
      </div>

      <div class="form-item">
        <label>补充说明</label>
        <textarea v-model.trim="form.remark" rows="3" placeholder="可填写驾龄、常用路线等信息，可选"></textarea>
      </div>

      <van-button type="primary" block :loading="submitting" @click="submitApplication">
        提交车主认证申请
      </van-button>
    </section>

    <section v-else-if="status === 'pending'" class="page-card state-card">
      <van-tag type="warning" size="large">审核中</van-tag>
      <h3>车主申请已提交</h3>
      <p class="hint">请等待管理员在“用户管理”中审核。审核通过后，刷新本页即可继续新增车辆。</p>
      <div class="action-grid">
        <van-button type="primary" plain block :loading="loadingProfile" @click="loadProfile">
          刷新审核状态
        </van-button>
        <van-button type="default" plain block to="/me/profile">
          返回个人中心
        </van-button>
      </div>
    </section>

    <section v-else-if="isApproved" class="page-card state-card">
      <van-tag type="success" size="large">已通过</van-tag>
      <h3>已具备车主资格</h3>
      <p class="hint">现在可以新增车辆。新增车辆时会同时提交车辆认证资料，提交后等待管理员在“车辆审核”中处理。</p>

      <div class="info-panel">
        <div class="info-row">
          <span>真实姓名</span>
          <b>{{ profile.real_name || form.real_name || '-' }}</b>
        </div>
        <div class="info-row">
          <span>车主信誉</span>
          <b>{{ profile.driver_score ?? 100 }} 分</b>
        </div>
        <div class="info-row">
          <span>名下车辆</span>
          <b>{{ vehicles.length }} 辆</b>
        </div>
      </div>

      <div class="action-grid">
        <van-button type="primary" block @click="goVehicleCenter">
          {{ vehicles.length ? '管理车辆认证' : '新增车辆并提交认证' }}
        </van-button>
        <van-button plain type="primary" block @click="enterDriverMode">
          进入车主首页
        </van-button>
      </div>
    </section>

    <section v-else-if="status === 'banned'" class="page-card state-card">
      <van-tag type="danger" size="large">已停用</van-tag>
      <h3>车主权限已停用</h3>
      <p class="hint">当前账号暂不能使用车主能力，请联系管理员处理。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showNotify } from 'vant'
import { fetchOwnerVehicles } from '../../api/ride'

const router = useRouter()
const loadingProfile = ref(true)
const submitting = ref(false)
const status = ref('unapplied')
const profile = ref({})
const vehicles = ref([])

const form = ref({
  real_name: '',
  id_card: '',
  driver_license_no: '',
  contact_phone: '',
  remark: ''
})

const isApplied = computed(() => status.value !== 'unapplied' && status.value !== 'loading')
const isApproved = computed(() => ['approved', 'active'].includes(status.value))

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

function saveSession(session) {
  localStorage.setItem('session', JSON.stringify(session))
  window.dispatchEvent(new Event('session-updated'))
}

function certStorageKey(userId) {
  return `driver-cert-${userId || 'anonymous'}`
}

function loadStoredCertification(userId) {
  try {
    return JSON.parse(localStorage.getItem(certStorageKey(userId)) || '{}')
  } catch {
    return {}
  }
}

function saveStoredCertification(userId) {
  localStorage.setItem(certStorageKey(userId), JSON.stringify(form.value))
}

function hydrateForm(data = {}) {
  const session = getSession()
  const saved = loadStoredCertification(session.userId)
  form.value = {
    real_name: saved.real_name || data.real_name || '',
    id_card: saved.id_card || data.id_card || '',
    driver_license_no: saved.driver_license_no || '',
    contact_phone: saved.contact_phone || data.phone || '',
    remark: saved.remark || ''
  }
}

async function loadVehiclesIfAllowed() {
  vehicles.value = []
  if (!isApproved.value) return

  try {
    const data = await fetchOwnerVehicles()
    vehicles.value = Array.isArray(data.items) ? data.items : []
  } catch {
    vehicles.value = []
  }
}

async function loadProfile() {
  const session = getSession()
  if (!session.userId) {
    router.push('/login')
    return
  }

  loadingProfile.value = true
  try {
    const res = await fetch(`/api/users/profile/${session.userId}`)
    if (!res.ok) throw new Error('profile load failed')

    const data = await res.json()
    profile.value = data
    status.value = data.driver_status || 'unapplied'
    hydrateForm(data)

    if (isApproved.value && !session.ownerVerified) {
      session.ownerVerified = true
      saveSession(session)
    }

    await loadVehiclesIfAllowed()
  } catch {
    status.value = session.ownerVerified ? 'approved' : 'unapplied'
    hydrateForm()
    await loadVehiclesIfAllowed()
  } finally {
    loadingProfile.value = false
  }
}

function validateApplication() {
  if (!form.value.real_name || !form.value.id_card || !form.value.driver_license_no) {
    return '请填写真实姓名、身份证号和驾驶证号'
  }
  if (!/^\d{17}[\dXx]$/.test(form.value.id_card)) {
    return '身份证号格式不正确'
  }
  return ''
}

async function submitApplication() {
  const message = validateApplication()
  if (message) {
    showNotify({ type: 'warning', message })
    return
  }

  const session = getSession()
  if (!session.userId) {
    router.push('/login')
    return
  }

  submitting.value = true
  try {
    const res = await fetch(`/api/users/driver/apply/${session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      throw new Error(data.detail || '申请提交失败')
    }

    saveStoredCertification(session.userId)
    session.ownerVerified = false
    saveSession(session)
    status.value = 'pending'
    showNotify({ type: 'success', message: '车主认证申请已提交' })
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '申请提交失败' })
  } finally {
    submitting.value = false
  }
}

function goVehicleCenter() {
  router.push('/me/vehicles')
}

function enterDriverMode() {
  const session = getSession()
  session.role = 'driver'
  session.ownerVerified = true
  saveSession(session)
  router.push('/driver/home')
}

onMounted(loadProfile)
</script>

<style scoped>
.driver-cert-page {
  display: grid;
  gap: 12px;
  padding-bottom: 24px;
}

.hero-card,
.form-card,
.state-card {
  display: grid;
  gap: 12px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 800;
}

h2,
h3 {
  margin: 0;
  color: #172033;
}

h2 {
  font-size: 22px;
}

h3 {
  font-size: 18px;
}

.page-hint,
.hint {
  margin: 0;
  color: #65758b;
  font-size: 13px;
  line-height: 1.6;
}

.flow-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid #dce8ff;
  border-radius: 14px;
  background: #f8fbff;
}

.flow-step {
  min-width: 62px;
  display: grid;
  justify-items: center;
  gap: 5px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 800;
}

.flow-step span {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eaf2ff;
  color: #6b88b8;
}

.flow-step.active,
.flow-step.done {
  color: #165dff;
}

.flow-step.active span,
.flow-step.done span {
  background: #165dff;
  color: #fff;
}

.flow-line {
  flex: 1;
  height: 1px;
  background: #dbe7ff;
}

.form-item {
  display: grid;
  gap: 6px;
}

.form-item label {
  color: #52657d;
  font-size: 13px;
  font-weight: 700;
}

.form-item input,
.form-item textarea {
  width: 100%;
  border: 1px solid #d8e2f0;
  border-radius: 10px;
  padding: 10px 12px;
  color: #172033;
  font-size: 14px;
  outline: none;
}

.form-item input:focus,
.form-item textarea:focus {
  border-color: #165dff;
  box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.1);
}

.state-card {
  text-align: center;
  justify-items: center;
  padding: 24px 16px;
}

.info-panel {
  width: 100%;
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid #edf3ff;
  background: #f8fbff;
  text-align: left;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #64748b;
  font-size: 13px;
}

.info-row b {
  color: #172033;
}

.action-grid {
  width: 100%;
  display: grid;
  gap: 8px;
}
</style>
