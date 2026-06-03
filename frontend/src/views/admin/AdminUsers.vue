<template>
  <div class="admin-users-page">
    <section class="page-card hero-card">
      <div>
        <div class="eyebrow">Admin Console</div>
        <h2>车主申请审核</h2>
        <p>这里只处理车主身份认证申请。乘客封禁属于更重的风控能力，先不放在普通管理入口里。</p>
      </div>
      <van-button size="small" plain type="primary" :loading="loading" @click="fetchUsers">
        刷新
      </van-button>
    </section>

    <section class="stat-row">
      <div class="stat-card">
        <span>待审核</span>
        <b>{{ pendingUsers.length }}</b>
      </div>
      <div class="stat-card">
        <span>已通过</span>
        <b>{{ approvedCount }}</b>
      </div>
      <div class="stat-card">
        <span>全部账号</span>
        <b>{{ manageableUsers.length }}</b>
      </div>
    </section>

    <section class="page-card">
      <div class="section-head">
        <h3>待审核申请</h3>
        <span>{{ pendingUsers.length }} 条</span>
      </div>

      <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
      <van-empty v-else-if="pendingUsers.length === 0" description="暂无待审核车主申请" />

      <div v-else class="review-list">
        <article v-for="user in pendingUsers" :key="user.userId" class="review-card">
          <div class="user-main">
            <div>
              <div class="user-name">{{ user.username }}</div>
              <div class="user-id">用户 ID：{{ user.userId }}</div>
            </div>
            <van-tag type="warning">审核中</van-tag>
          </div>

          <div class="actions">
            <van-button
              size="small"
              type="success"
              :loading="operatingId === user.userId"
              @click="reviewDriver(user, 'approved')"
            >
              通过
            </van-button>
            <van-button
              size="small"
              type="danger"
              plain
              :loading="operatingId === user.userId"
              @click="reviewDriver(user, 'unapplied')"
            >
              驳回
            </van-button>
          </div>
        </article>
      </div>
    </section>

    <section class="page-card">
      <div class="section-head">
        <h3>用户概览</h3>
        <span>只读</span>
      </div>

      <div class="compact-list">
        <article v-for="user in manageableUsers" :key="user.userId" class="compact-row">
          <div>
            <div class="compact-name">{{ user.username }}</div>
            <div class="compact-id">ID #{{ user.userId }}</div>
          </div>
          <van-tag :type="driverTagType(user.driver_status)">
            {{ driverStatusText(user.driver_status) }}
          </van-tag>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { showConfirmDialog, showNotify } from 'vant'

const userList = ref([])
const loading = ref(false)
const operatingId = ref(null)

const manageableUsers = computed(() => userList.value.filter((user) => user.username !== 'admin'))
const pendingUsers = computed(() => manageableUsers.value.filter((user) => user.driver_status === 'pending'))
const approvedCount = computed(() =>
  manageableUsers.value.filter((user) => ['approved', 'active'].includes(user.driver_status)).length
)

onMounted(fetchUsers)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await fetch('/api/users/admin/users')
    if (!res.ok) throw new Error('用户列表加载失败')
    const data = await res.json()
    userList.value = Array.isArray(data.items) ? data.items : []
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '用户列表加载失败' })
  } finally {
    loading.value = false
  }
}

function driverStatusText(status) {
  return ({
    unapplied: '未申请',
    pending: '审核中',
    approved: '已通过',
    active: '已通过',
    banned: '已停用'
  })[status] || status
}

function driverTagType(status) {
  if (status === 'pending') return 'warning'
  if (status === 'approved' || status === 'active') return 'success'
  if (status === 'banned') return 'danger'
  return 'default'
}

async function reviewDriver(user, nextStatus) {
  const actionText = nextStatus === 'approved' ? '通过' : '驳回'
  try {
    await showConfirmDialog({
      title: `${actionText}车主申请`,
      message: `确认${actionText}用户「${user.username}」的车主认证申请吗？`
    })
  } catch {
    return
  }

  operatingId.value = user.userId
  try {
    const res = await fetch('/api/users/admin/update-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId: user.userId,
        target_identity: 'driver',
        new_status: nextStatus
      })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || '审核操作失败')

    showNotify({ type: 'success', message: nextStatus === 'approved' ? '已通过车主申请' : '已驳回车主申请' })
    await fetchUsers()
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '审核操作失败' })
  } finally {
    operatingId.value = null
  }
}
</script>

<style scoped>
.admin-users-page {
  display: grid;
  gap: 12px;
  padding-bottom: 28px;
}

.hero-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 5px;
}

h2,
h3,
p {
  margin: 0;
}

h2 {
  color: #172033;
  font-size: 22px;
}

h3 {
  color: #172033;
  font-size: 16px;
}

p {
  margin-top: 7px;
  color: #65758b;
  font-size: 13px;
  line-height: 1.55;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  padding: 13px 10px;
  border: 1px solid #dce8ff;
  border-radius: 16px;
  background: #fff;
  text-align: center;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.06);
}

.stat-card span {
  display: block;
  color: #7b8aa1;
  font-size: 12px;
}

.stat-card b {
  display: block;
  margin-top: 4px;
  color: #165dff;
  font-size: 24px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-head span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 36px 0;
}

.review-list,
.compact-list {
  display: grid;
  gap: 10px;
}

.review-card,
.compact-row {
  border: 1px solid #e5edf9;
  border-radius: 14px;
  padding: 12px;
  background: #fbfdff;
}

.user-main,
.compact-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.user-name,
.compact-name {
  color: #172033;
  font-weight: 800;
}

.user-id,
.compact-id {
  margin-top: 3px;
  color: #8a97ac;
  font-size: 12px;
}

.actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 420px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
