<template>
  <div class="app-container">
    
    <![WYX-START] 账号域改动：顶部导航栏实现角色动态感知与身份切换 -->
    <header class="app-header">
      <div class="header-content">
        <span class="app-logo">拼车出行</span>
        <div class="user-status-area">
          <!-- 1. 动态角色标签：根据 session.role 自动显示 -->
          <span v-if="currentRole" :class="['role-badge', currentRole]">
            {{ getRoleLabel(currentRole) }}
          </span>

          <span class="username-display">{{ username }}</span>

          <!-- 2. 身份切换按钮：只有已通过车主认证的用户才显示，实现乘客/车主一键切模式 -->
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
    <!-- [WYX-END] -->

    <!-- 中间内容区（各功能域页面占位） -->
    <main class="app-main">
      <router-view />
    </main>

    <![WYX-START] 账号域改动：底部菜单根据 session.role 权限过滤 -->
 
    <footer class="app-footer">
      
      <!-- 管理员专属菜单 -->
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
    <!-- [WYX-END] -->

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// WYX:账号域逻辑：身份状态管理、多角色切换、路由同步
const currentRole = ref('')
const username = ref('')
const isVerifiedDriver = ref(false) // 标记当前账号是否拥有车主权限

// 菜单配置
const adminMenus = [
  { name: '用户管理', path: '/admin/users' },
  { name: '订单监控', path: '/admin/orders' },
  { name: '投诉处理', path: '/admin/feedback' }
]

const passengerMenus = [
  { name: '首页', path: '/passenger/home' },
  { name: '我的订单', path: '/passenger/orders/mine' },
  { name: '认证车主', path: '/driver/certification' }
]

const driverMenus = [
  { name: '接单大厅', path: '/driver/home' },
  { name: '行程管理', path: '/driver/orders/mine' },
  { name: '我的车辆', path: '/driver/vehicles' }
]

/**
 * 同步身份信息：从 LocalStorage 读取由 LoginPage 存入的 session
 * 解决“右上角显示错误”及“角色越权切换”问题
 */
const syncIdentity = () => {
  const sessionStr = localStorage.getItem('session')
  if (sessionStr) {
    const session = JSON.parse(sessionStr)
    currentRole.value = session.role
    username.value = session.username
    // 关键：读取认证标志位。如果是true，则允许显示“切换身份”按钮
    isVerifiedDriver.value = session.ownerVerified === true
  } else {
    router.push('/login')
  }
}

/**
 * 核心功能：身份一键切换 (乘客 <-> 车主)
 * 不改动数据库认证状态，仅修改前端工作模式 role 字段
 */
const handleSwitchRole = () => {
  const session = JSON.parse(localStorage.getItem('session'))
  
  if (currentRole.value === 'driver') {
    session.role = 'passenger'
    alert('已进入拼车人模式')
    router.push('/passenger/home').then(() => window.location.reload())
  } else {
    session.role = 'driver'
    alert('已进入车主模式')
    router.push('/driver/home').then(() => window.location.reload())
  }
  
  localStorage.setItem('session', JSON.stringify(session))
}

const getRoleLabel = (role) => {
  const labels = { 'admin': '管理员', 'passenger': '拼车人', 'driver': '认证车主' }
  return labels[role] || '游客'
}

/**
 * 安全退出：清理账号域敏感缓存
 */
const handleLogout = () => {
  if (confirm('确定要退出账号吗？')) {
    localStorage.removeItem('session')
    router.push('/login')
  }
}

// 初始化及路由监听：确保用户手动修改URL时 UI 依然同步
onMounted(syncIdentity)
watch(() => route.path, syncIdentity)

// [END]
// ------------------------------------------------------------
</script>

<style scoped>
.app-container { display: flex; flex-direction: column; height: 100vh; }

/* [WYX] 顶部导航样式优化 */
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

/* 身份切换按钮样式 */
.switch-btn {
  background: #fff;
  border: 1px solid #1890ff;
  color: #1890ff;
  padding: 2px 10px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 11px;
  margin-right: 10px;
  transition: all 0.3s;
}
.switch-btn:hover { background: #1890ff; color: #fff; }

.role-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 8px; font-weight: bold; }
.role-badge.admin { background: #fff1f0; color: #f5222d; border: 1px solid #ffa39e; }
.role-badge.passenger { background: #e6f7ff; color: #1890ff; border: 1px solid #91d5ff; }
.role-badge.driver { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }

.username-display { font-size: 14px; color: #666; margin-right: 12px; }
.logout-btn { border: 1px solid #d9d9d9; background: #fff; padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; color: #999; }

.app-main { flex: 1; overflow-y: auto; background: #f0f2f5; padding-bottom: 70px; }

/* 底部导航菜单样式 */
.app-footer {
  background: #fff;
  height: 60px;
  border-top: 1px solid #f0f0f0;
  position: fixed;
  bottom: 0;
  width: 100%;
  z-index: 100;
}
.nav-menu { display: flex; height: 100%; justify-content: space-around; align-items: center; }
.nav-item { text-decoration: none; color: #8c8c8c; display: flex; flex-direction: column; align-items: center; }
.nav-text { font-size: 12px; margin-top: 4px; }

/* 菜单激活高亮 */
.router-link-active { color: #1890ff; font-weight: bold; }
</style>