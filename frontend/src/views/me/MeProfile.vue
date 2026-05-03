<template>
  <div class="me-page">
    <section class="page-card profile-card">
      <div>
        <div class="eyebrow">个人中心</div>
        <h2>{{ session.username || '未命名用户' }}</h2>
        <p>登录后默认以拼车人身份使用，车主资格通过后可切换到车主模式。</p>
      </div>
      <van-tag :type="session.ownerVerified ? 'success' : 'warning'">
        {{ session.ownerVerified ? '已具备车主资格' : '拼车人' }}
      </van-tag>
    </section>

    <section class="page-card action-list">
      <router-link to="/me/driver-application" class="action-row">
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
.me-page { display: grid; gap: 12px; }
.profile-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 4px;
}
h2 { margin: 0 0 6px; font-size: 22px; color: #172033; }
p { margin: 0; color: #65758b; font-size: 13px; line-height: 1.6; }
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
</style>
