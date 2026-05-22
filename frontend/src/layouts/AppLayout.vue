<template>
  <div class="app-container">
    
    <!-- [WYX] 顶部导航栏 -->
    <header class="app-header">
      <div class="header-content">
        <span class="app-logo">拼车出行</span>
        <div class="user-status-area">
          <!-- 动态角色标签 -->
          <span v-if="currentRole" :class="['role-badge', currentRole]">
            {{ getRoleLabel(currentRole) }}
          </span>

          <span class="username-display">{{ username }}</span>

          <!-- 身份切换按钮：只有已认证车主可见 -->
          <button 
            v-if="isVerifiedDriver" 
            class="switch-btn" 
            @click="handleSwitchRole"
          >
            {{ currentRole === 'driver' ? '切回拼车人' : '切换为车主' }}
          </button>

          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>

    <!-- 内容区 -->
    <main class="app-main">
      <router-view />
    </main>

    <!-- [WYX] 底部导航菜单 -->
    <footer class="app-footer">
      <!-- 管理员底部菜单 -->
      <nav v-if="currentRole === 'admin'" class="nav-menu">
        <router-link v-for="item in adminMenus" :key="item.path" :to="item.path" class="nav-item">
          <span class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- 拼车人(乘客)专属菜单 -->
      <nav v-else-if="currentRole === 'passenger'" class="nav-menu">
        <router-link v-for="item in passengerMenus" :key="item.path" :to="item.path" class="nav-item">
          <span class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- 车主(司机)专属菜单 -->
      <nav v-else-if="currentRole === 'driver'" class="nav-menu">
        <router-link v-for="item in driverMenus" :key="item.path" :to="item.path" class="nav-item">
          <span class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>
    </footer>

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue' // [修正] 之前漏掉了 computed 等导入，但由于你没用到组长的 computed，我帮你精简了
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// --- [WYX] 核心逻辑：定义 getSession 函数解决报错 ---
const getSession = () => {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch (e) {
    return {}
  }
}

const currentRole = ref('')
const username = ref('')
const isVerifiedDriver = ref(false)

// 菜单配置
const adminMenus = [
  { name: '用户管理', path: '/admin/users' },
  { name: '订单监控', path: '/admin/orders' },
  { name: '投诉处理', path: '/admin/feedback' }
]
const passengerMenus = [
  { name: '首页', path: '/passenger/home' },
  { name: '我的订单', path: '/passenger/orders/mine' },
  { name: '我的钱包', path: '/passenger/wallet' },       // yzr
  { name: '认证车主', path: '/driver/certification' }
]
const driverMenus = [
  { name: '接单大厅', path: '/driver/home' },
  { name: '行程管理', path: '/driver/orders/mine' },
  { name: '我的车辆', path: '/driver/vehicles' },
  { name: '钱包提现', path: '/driver/wallet' }            // yzr
]

/**
 * [WYX] 同步身份状态
 */
const syncIdentity = () => {
  const session = getSession()
  if (session.token) {
    currentRole.value = session.role
    username.value = session.username
    isVerifiedDriver.value = session.ownerVerified === true
  } else {
    router.push('/login')
  }
}

/**
 * [WYX] 身份一键切换
 */
const handleSwitchRole = () => {
  const session = getSession()
  if (currentRole.value === 'driver') {
    session.role = 'passenger'
    alert('已进入拼车人模式')
    localStorage.setItem('session', JSON.stringify(session))
    router.push('/passenger/home').then(() => window.location.reload())
  } else {
    session.role = 'driver'
    alert('已进入车主模式')
    localStorage.setItem('session', JSON.stringify(session))
    router.push('/driver/home').then(() => window.location.reload())
  }
}

const getRoleLabel = (role) => {
  const labels = { 'admin': '管理员', 'passenger': '拼车人', 'driver': '车主' }
  return labels[role] || '游客'
}

/**
 * [WYX] 退出登录
 */
const handleLogout = () => {
  if (confirm('确定要退出账号吗？')) {
    localStorage.removeItem('session')
    router.push('/login')
  }
}

onMounted(syncIdentity)
watch(() => route.path, syncIdentity)
</script>

<style scoped>
/* 样式保持你之前的即可 */
.app-container { display: flex; flex-direction: column; height: 100vh; }
.app-header {
  background: #fff;
  padding: 0 15px;
  height: 50px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  z-index: 100;
}
.header-content { display: flex; justify-content: space-between; width: 100%; align-items: center; }
.app-logo { font-weight: bold; color: #333; font-size: 18px; }
.switch-btn {
  background: #fff;
  border: 1px solid #1890ff;
  color: #1890ff;
  padding: 2px 10px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 11px;
  margin-right: 10px;
}
.role-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 8px; font-weight: bold; }
.role-badge.admin { background: #fff1f0; color: #f5222d; }
.role-badge.passenger { background: #e6f7ff; color: #1890ff; }
.role-badge.driver { background: #f6ffed; color: #52c41a; }
.username-display { font-size: 14px; color: #666; margin-right: 12px; }
.logout-btn { border: 1px solid #d9d9d9; background: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #999; }
.app-main { flex: 1; overflow-y: auto; background: #f0f2f5; padding-bottom: 70px; }
.app-footer {
  background: #fff;
  height: 60px;
  border-top: 1px solid #f0f0f0;
  position: fixed;
  bottom: 0;
  width: 100%;
}
.nav-menu { display: flex; height: 100%; justify-content: space-around; align-items: center; }
.nav-item { text-decoration: none; color: #8c8c8c; display: flex; flex-direction: column; align-items: center; }
.nav-text { font-size: 12px; margin-top: 4px; }
.router-link-active { color: #1890ff; font-weight: bold; }
</style>
