<!--全局模板：
<template>：页面结构，模拟手机屏幕
<script setup>：逻辑代码
<style scoped>：局部样式，只影响本组件-->
<template>
  <div class="mobile-app"> <!--居中显示手机框架-->
    <section class="phone-frame"> <!--模拟手机屏幕，固定宽度（移动端最大 420px，PC 端有圆角阴影）-->
      <van-nav-bar :title="navTitle">
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

      <van-tabbar route>
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
import { computed, ref } from 'vue'
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

function setSession(session) {
  localStorage.setItem('session', JSON.stringify(session))
}

const session = computed(() => getSession())

const roleLabel = computed(() => {
  if (session.value.role === 'admin') return '管理员'
  if (session.value.ownerVerified) return '车主(已认证)'
  return '拼车人'
})

const tabItems = computed(() => {
  if (session.value.role === 'admin') {
    return [
      { path: '/admin/users', label: '用户', icon: 'manager-o' },
      { path: '/admin/orders', label: '订单', icon: 'todo-list-o' },
      { path: '/admin/feedback', label: '反馈', icon: 'chat-o' }
    ]
  }

  if (session.value.ownerVerified && router.currentRoute.value.path.startsWith('/driver')) {
    return [
      { path: '/driver/home', label: '首页', icon: 'home-o' },
      { path: '/driver/orders/available', label: '接单', icon: 'fire-o' },
      { path: '/driver/orders/mine', label: '我的', icon: 'notes-o' },
      { path: '/driver/wallet', label: '钱包', icon: 'balance-o' }
    ]
  }

  return [
    { path: '/passenger/home', label: '首页', icon: 'home-o' },
    { path: '/passenger/orders/publish', label: '发布', icon: 'plus' },
    { path: '/passenger/orders/search', label: '搜索', icon: 'search' },
    { path: '/passenger/orders/mine', label: '我的', icon: 'notes-o' }
  ]
})

const navTitle = computed(() => {
  const path = router.currentRoute.value.path
  if (path.startsWith('/admin')) return '管理员工作台'
  if (path.startsWith('/driver')) return '车主拼车'
  return '拼车出行'
})

const actionItems = [
  { text: '切换拼车人', key: 'passenger' },
  { text: '切换车主', key: 'driver' },
  { text: '切换管理员', key: 'admin' },
  { text: '退出登录', key: 'logout' }
]

function onActionSelect(action) {
  if (action.key === 'logout') {
    logout()
    return
  }
  switchRole(action.key)
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
    current.role = 'user'
    current.ownerVerified = true
    current.token = current.token || 'dev-token'
    setSession(current)
    router.push('/driver/home')
    return
  }

  current.role = 'user'
  current.ownerVerified = false
  current.token = current.token || 'dev-token'
  setSession(current)
  router.push('/passenger/home')
}

function logout() {
  localStorage.removeItem('session')
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
  min-height: 100vh;
  background: #ffffff;
  box-shadow: 0 14px 36px rgba(10, 40, 90, 0.15);
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 12px 70px;
}

@media (min-width: 760px) {
  .phone-frame {
    min-height: 92vh;
    border-radius: 22px;
    overflow: hidden;
  }
}
</style>
