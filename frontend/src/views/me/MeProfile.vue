<template>
  <div class="me-page">
    <section class="page-card profile-card" :class="{ 'profile-card--owner': session.ownerVerified }">
      <div class="profile-main">
        <div class="eyebrow">个人中心</div>
        <h2>{{ session.username || '未命名用户' }}</h2>
        <p>
          {{ session.ownerVerified
            ? '已通过车主资格认证，可切换到车主模式并管理车辆。'
            : '登录后默认以拼车人身份使用，通过认证后可切换到车主模式。' }}
        </p>
      </div>
      <div class="identity-badge" :class="{ 'identity-badge--owner': session.ownerVerified }">
        <span class="badge-dot"></span>
        <span>{{ session.ownerVerified ? '已具备车主资格' : '拼车人' }}</span>
      </div>
    </section>

    <section class="page-card action-list">
      <router-link v-if="!session.ownerVerified" to="/me/driver-application" class="action-row">
        <span>车主身份认证</span><b>></b>
      </router-link>
      <router-link to="/me/vehicles" class="action-row">
        <span>我的车辆</span><b>></b>
      </router-link>
      <router-link to="/me/messages" class="action-row">
        <span>消息与沟通</span><b>></b>
      </router-link>
      <router-link to="/me/feedback" class="action-row">
        <span>我的反馈</span><b>></b>
      </router-link>
      <router-link to="/me/security" class="action-row">
        <span>账号安全</span><b>></b>
      </router-link>
    </section>
  </div>
</template>

<script setup>
function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

const session = getSession()
</script>

<style scoped>
.me-page {
  display: grid;
  gap: 12px;
}

.profile-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  position: relative;
  overflow: hidden;
  padding: 18px 16px;
  border: 1px solid #dbeafe;
  background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
  box-shadow: 0 10px 24px rgba(22, 93, 255, 0.08);
}

.profile-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: #165dff;
}

.profile-card--owner {
  border-color: #bbf7d0;
  background: linear-gradient(135deg, #f7fffb 0%, #eff6ff 100%);
}

.profile-card--owner::before {
  background: #10b981;
}

.profile-main {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
}

h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
  color: #172033;
}

p {
  margin: 0;
  color: #52657d;
  font-size: 13px;
  line-height: 1.65;
}

.identity-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  max-width: 126px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #fed7aa;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.25;
  box-shadow: 0 6px 14px rgba(249, 115, 22, 0.12);
}

.identity-badge--owner {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #047857;
  box-shadow: 0 6px 14px rgba(16, 185, 129, 0.14);
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  flex: 0 0 auto;
}

.action-list { display: grid; padding: 4px 14px; }
.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  color: #172033;
  text-decoration: none;
  border-bottom: 1px solid #edf1f7;
  font-weight: 600;
}
.action-row:last-child { border-bottom: none; }
.action-row b { color: #9aa8ba; }

@media (max-width: 360px) {
  .profile-card {
    flex-direction: column;
  }

  .identity-badge {
    max-width: none;
  }
}
</style>
