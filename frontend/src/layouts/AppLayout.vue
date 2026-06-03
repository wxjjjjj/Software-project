<!--全局模板：
<template>：页面结构，模拟手机屏幕
<script setup>：逻辑代码
<style scoped>：局部样式，只影响本组件-->
<template>
  <div class="mobile-app"> <!--居中显示手机框架-->
    <section class="phone-frame"> <!--模拟手机屏幕，固定宽度（移动端最大 420px，PC 端有圆角阴影）-->
      <van-nav-bar :title="navTitle" :left-arrow="showBackArrow" @click-left="handleNavBack">
        <template #right>
          <van-popover v-model:show="showActionMenu" :actions="actionItems" @select="onActionSelect">
            <template #reference>
              <van-button size="small" plain type="primary">{{ roleLabel }}</van-button>
            </template>
          </van-popover>
        </template>
      </van-nav-bar>

      <main class="content">
        <RouterView />
      </main>

      <van-tabbar route :fixed="false">
        <van-tabbar-item
          v-for="item in tabItems"
          :key="item.path"
          :to="item.path"
          :icon="item.icon"
        >
          {{ item.label }}
        </van-tabbar-item>
      </van-tabbar>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showActionMenu = ref(false)

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

function setSession(s) {
  localStorage.setItem('session', JSON.stringify(s))
  session.value = s  // 同步更新响应式引用
}

const session = ref(getSession())

function syncSession() {
  session.value = getSession()
}

watch(
  () => router.currentRoute.value.fullPath,
  syncSession,
)

onMounted(() => {
  window.addEventListener('storage', syncSession)
  window.addEventListener('session-updated', syncSession)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', syncSession)
  window.removeEventListener('session-updated', syncSession)
})

const roleLabel = computed(() => {
  if (session.value.role === 'admin') return '管理员'
  if (session.value.role === 'driver') return '司机'
  return '乘客'
})

const tabItems = computed(() => {
  if (session.value.role === 'admin') {
    return [
      { path: '/admin/users', label: '用户', icon: 'manager-o' },
      { path: '/admin/orders', label: '订单', icon: 'todo-list-o' },
      { path: '/admin/vehicle-verifications', label: '车辆审核', icon: 'logistics' },
      { path: '/admin/feedback', label: '投诉', icon: 'chat-o' }
    ]
  }

  if (session.value.role === 'driver' && session.value.ownerVerified) {
    return [
      { path: '/driver/home', label: '首页', icon: 'home-o' },
      { path: '/driver/orders/available', label: '接单', icon: 'fire-o' },
      { path: '/driver/orders/mine', label: '行程', icon: 'notes-o' },
      { path: '/me/vehicles', label: '车辆', icon: 'logistics' },
      { path: '/me/profile', label: '我的', icon: 'user-o' }
    ]
  }

  return [
    { path: '/passenger/home', label: '首页', icon: 'home-o' },
    { path: '/passenger/orders/publish', label: '发布', icon: 'plus' },
    { path: '/passenger/orders/search', label: '搜索', icon: 'search' },
    { path: '/passenger/orders/mine', label: '订单', icon: 'notes-o' },
    { path: '/me/profile', label: '我的', icon: 'user-o' }
  ]
})

const navTitle = computed(() => {
  const path = router.currentRoute.value.path
  if (path.includes('/chat/')) return '订单聊天'
  if (path.startsWith('/admin')) return '管理员工作台'
  if (path.startsWith('/driver')) return '车主钱包'
  if (path.startsWith('/me')) return '我的'
  if (path.startsWith('/users')) return '用户资料'
  return '拼车出行'
})

const showBackArrow = computed(() => Boolean(router.currentRoute.value.meta.backTo))

const actionItems = computed(() => {
  if (session.value.role === 'admin') {
    return [
      { text: '管理员工作台', key: 'admin' },
      { text: '退出登录', key: 'logout' }
    ]
  }

  const items = [
    { text: '乘客模式', key: 'passenger' },
    { text: session.value.ownerVerified ? '司机模式' : '申请成为车主', key: 'driver' },
    { text: '个人中心', key: 'me' }
  ]
  if (session.value.role === 'admin') {
    items.unshift({ text: '管理员工作台', key: 'admin' })
  }
  items.push({ text: '退出登录', key: 'logout' })
  return items
})

function onActionSelect(action) {
  if (action.key === 'logout') {
    logout()
    return
  }
  if (action.key === 'me') {
    router.push('/me/profile')
    return
  }
  switchRole(action.key)
}

function handleNavBack() {
  if (!showBackArrow.value) return

  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push(router.currentRoute.value.meta.backTo || '/')
}

//后续可以把角色切换降级为仅开发环境可见，权限以登录接口返回为准
//当前由登录页调用后端认证接口，再把后端返回的身份信息写入session
function switchRole(target) {
  const current = getSession()

  if (target === 'admin') {
    current.role = 'admin'
    current.token = current.token || 'dev-token'
    setSession(current)
    router.push('/admin/users')
    return
  }

  if (target === 'driver') {
    if (!current.ownerVerified) {
      setSession(current)
      router.push('/me/driver-application')
      return
    }
    current.role = 'driver'
    current.token = current.token || 'dev-token'
    setSession(current)
    router.push('/driver/home')
    return
  }

  current.role = 'passenger'
  current.token = current.token || 'dev-token'
  setSession(current)
  router.push('/passenger/home')
}

function logout() {
  localStorage.removeItem('session')
  session.value = {}
  router.push('/login')
}
</script>

<style scoped>
.mobile-app {
  display: grid;
  place-items: center;
  min-height: 100vh;
  background: radial-gradient(circle at 20% 0%, #d8ecff 0%, #f5f8ff 42%, #f6f8fb 100%);
}

.phone-frame {
  width: min(100%, 420px);
  height: 100vh;
  background: #ffffff;
  box-shadow: 0 14px 36px rgba(10, 40, 90, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform: translateZ(0);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

@media (min-width: 760px) {
  .phone-frame {
    height: 844px;
    border-radius: 22px;
  }
}
</style>
