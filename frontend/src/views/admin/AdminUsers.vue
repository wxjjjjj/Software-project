<template>
  <div class="admin-users-page">
    <section class="page-hero">
      <div class="hero-copy">
        <p class="hero-eyebrow">Admin Console</p>
        <h1>用户管理</h1>
        <p class="hero-subtitle">查看账号状态，并进行乘客/车主身份管理。</p>
      </div>

      <div class="hero-actions">
        <div class="count-card">
          <span class="count-label">当前账号</span>
          <strong>{{ userList.length }}</strong>
        </div>
        <button class="refresh-btn" :disabled="loading" @click="fetchUsers">
          <span class="refresh-icon">↻</span>
          {{ loading ? '刷新中' : '刷新' }}
        </button>
      </div>
    </section>

    <section v-if="userList.length" class="user-list">
      <article
        v-for="(user, index) in userList"
        :key="user.userId"
        class="user-card"
        :style="{ animationDelay: `${index * 0.04}s` }"
      >
        <div class="user-card-head">
          <div class="user-main">
            <div class="user-name-row">
              <h2>{{ user.username }}</h2>
              <span v-if="user.username === 'admin'" class="admin-badge">系统管理员</span>
            </div>
            <div class="user-id">ID #{{ user.userId }}</div>
          </div>

          <div v-if="user.username === 'admin'" class="system-lock">系统保留账号</div>
        </div>

        <div class="status-panel">
          <div class="status-item">
            <span class="status-label">乘客身份</span>
            <span :class="['status-chip', user.passenger_status]">
              {{ user.passenger_status === 'active' ? '正常' : '已封禁' }}
            </span>
          </div>

          <div class="status-item">
            <span class="status-label">车主身份</span>
            <span :class="['status-chip', user.driver_status]">
              {{ getDriverStatusText(user.driver_status) }}
            </span>
          </div>
        </div>

        <div v-if="user.username !== 'admin'" class="action-panel">
          <button
            class="action-btn danger-soft"
            @click="updateStatus(user.userId, 'passenger', user.passenger_status === 'active' ? 'banned' : 'active')"
          >
            {{ user.passenger_status === 'active' ? '封禁乘客' : '解封乘客' }}
          </button>

          <button
            v-if="user.driver_status !== 'unapplied' && user.driver_status !== 'pending'"
            class="action-btn"
            :class="isDriverEnabled(user.driver_status) ? 'danger-soft' : 'success-soft'"
            @click="updateStatus(user.userId, 'driver', isDriverEnabled(user.driver_status) ? 'banned' : 'active')"
          >
            {{ isDriverEnabled(user.driver_status) ? '封禁车主' : '解封车主' }}
          </button>
        </div>
      </article>
    </section>

    <section v-else-if="!loading" class="empty-state">
      <div class="empty-icon">◎</div>
      <h3>还没有可展示的用户</h3>
      <p>如果你刚启动服务，可以点一下刷新重新拉取数据。</p>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const userList = ref([])
const loading = ref(false)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await fetch('/api/users/admin/users')
    if (res.ok) {
      const data = await res.json()
      userList.value = Array.isArray(data.items) ? data.items : []
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function updateStatus(userId, identity, newStatus) {
  if (!confirm('确认修改该身份状态吗？')) return
  try {
    const res = await fetch('/api/users/admin/update-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, target_identity: identity, new_status: newStatus })
    })
    if (res.ok) {
      fetchUsers()
    }
  } catch (err) {
    alert('网络错误')
  }
}

function getDriverStatusText(status) {
  return ({
    unapplied: '未申请',
    pending: '审核中',
    approved: '已通过',
    active: '正常',
    banned: '已封禁'
  })[status] || status
}

function isDriverEnabled(status) {
  return status === 'active' || status === 'approved'
}

onMounted(fetchUsers)
</script>

<style scoped>
@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.admin-users-page {
  --ink-strong: #1f2a44;
  --ink-soft: #6b7a90;
  --line: #d9e6fb;
  --surface: #ffffff;
  --surface-alt: linear-gradient(180deg, #fdfefe 0%, #f5f8ff 100%);
  --blue-soft: #edf4ff;
  --blue-accent: #2563eb;
  --shadow-soft: 0 12px 28px rgba(37, 99, 235, 0.08);
  padding: 14px 14px 34px;
}

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--surface-alt);
  box-shadow: var(--shadow-soft);
}

.hero-copy {
  min-width: 0;
  flex: 1;
}

.hero-eyebrow {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7d8fb3;
}

.hero-copy h1 {
  margin: 0;
  font-size: 26px;
  line-height: 1.08;
  color: var(--ink-strong);
}

.hero-subtitle {
  margin: 8px 0 0;
  max-width: 240px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink-soft);
}

.hero-actions {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.count-card {
  min-width: 88px;
  padding: 10px 12px;
  border: 1px solid #d7e5ff;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  text-align: right;
}

.count-label {
  display: block;
  font-size: 11px;
  color: #7b8aa4;
}

.count-card strong {
  display: block;
  margin-top: 2px;
  font-size: 24px;
  line-height: 1;
  color: var(--blue-accent);
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 88px;
  padding: 10px 14px;
  border: 1px solid #cfe0ff;
  border-radius: 999px;
  background: #fff;
  color: var(--ink-strong);
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.refresh-btn:disabled {
  opacity: 0.7;
}

.refresh-btn:active {
  transform: scale(0.97);
}

.refresh-icon {
  color: var(--blue-accent);
  font-size: 14px;
  font-weight: 800;
}

.user-list {
  display: grid;
  gap: 12px;
}

.user-card {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  animation: cardEnter 0.28s ease both;
}

.user-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.user-main {
  min-width: 0;
  flex: 1;
}

.user-name-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.user-name-row h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.15;
  color: var(--ink-strong);
}

.user-id {
  margin-top: 6px;
  font-size: 12px;
  color: #8a97ac;
}

.admin-badge {
  padding: 4px 10px;
  border-radius: 999px;
  background: #24334f;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.system-lock {
  padding: 7px 10px;
  border-radius: 12px;
  background: #f5f7fb;
  color: #7f8ca3;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.status-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.status-item {
  padding: 12px;
  border: 1px solid #e8eefc;
  border-radius: 14px;
  background: #fbfcff;
}

.status-label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--ink-soft);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status-chip.active,
.status-chip.approved {
  background: #ebfbf4;
  border-color: #b9efcf;
  color: #18a35f;
}

.status-chip.banned {
  background: #fff1f1;
  border-color: #ffd5d5;
  color: #e64c4c;
}

.status-chip.pending {
  background: #fff7eb;
  border-color: #ffd8a8;
  color: #db7b11;
}

.status-chip.unapplied {
  background: #f2f5fa;
  border-color: #dbe3ef;
  color: #7e8aa0;
}

.action-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.action-btn {
  flex: 1 1 140px;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: #eef6ff;
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  transition: transform 0.16s ease, filter 0.16s ease;
}

.action-btn:active {
  transform: scale(0.98);
}

.danger-soft {
  background: #fff3f3;
  border-color: #ffdcdc;
  color: #e54848;
}

.success-soft {
  background: #eefbf3;
  border-color: #caefd6;
  color: #17915d;
}

.empty-state {
  padding: 42px 18px;
  border: 1px dashed #cfe0ff;
  border-radius: 20px;
  background: linear-gradient(180deg, #fbfdff 0%, #f3f7ff 100%);
  text-align: center;
}

.empty-icon {
  font-size: 28px;
  color: #7c92b9;
}

.empty-state h3 {
  margin: 10px 0 6px;
  font-size: 18px;
  color: var(--ink-strong);
}

.empty-state p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink-soft);
}

@media (max-width: 640px) {
  .page-hero {
    flex-direction: column;
  }

  .hero-subtitle {
    max-width: none;
  }

  .hero-actions {
    width: 100%;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: stretch;
    justify-items: stretch;
  }

  .count-card {
    text-align: left;
  }

  .status-panel {
    grid-template-columns: 1fr;
  }

  .action-panel {
    flex-direction: column;
  }
}
</style>
