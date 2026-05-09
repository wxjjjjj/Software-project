//路由总表
import { createRouter, createWebHistory } from 'vue-router'
//布局组件
import AppLayout from '../layouts/AppLayout.vue'
//所有需要用到的页面组件--目前暂定的这些，如果有添加/删除的需要记得跟wxj说，自己不要改
import LoginPage from '../views/common/LoginPage.vue'//wyx
import RegisterPage from '../views/common/RegisterPage.vue'//wyx
//出错页面
import NotFoundPage from '../views/common/NotFoundPage.vue'
import ForbiddenPage from '../views/common/ForbiddenPage.vue'
import UserProfile from '../views/common/UserProfile.vue'
//个人中心
import MeProfile from '../views/me/MeProfile.vue'
import MeDriverApplication from '../views/me/MeDriverApplication.vue'
import MeMessages from '../views/me/MeMessages.vue'
import MeFeedback from '../views/me/MeFeedback.vue'
import MeSecurity from '../views/me/MeSecurity.vue'
//乘客
import PassengerHome from '../views/passenger/PassengerHome.vue'//hws、zj
import PassengerOrderPublish from '../views/passenger/PassengerOrderPublish.vue'//hws、zj
import PassengerOrderSearch from '../views/passenger/PassengerOrderSearch.vue'//hws、zj
import PassengerOrderDetail from '../views/passenger/PassengerOrderDetail.vue'//hws、zj
import PassengerOrderMine from '../views/passenger/PassengerOrderMine.vue'//hws、zj
import PassengerPayment from '../views/passenger/PassengerPayment.vue'//yzr
import PassengerFeedback from '../views/passenger/PassengerFeedback.vue'//yzr
//车主owner/driver
import OwnerHome from '../views/owner/OwnerHome.vue'//hws、zj
import OwnerVehicles from '../views/owner/OwnerVehicles.vue'//hws、zj
import OwnerVehicleForm from '../views/owner/OwnerVehicleForm.vue'//zj
import OwnerVehicleVerify from '../views/owner/OwnerVehicleVerify.vue'//zj
import OwnerOrderAvailable from '../views/owner/OwnerOrderAvailable.vue'//hws、zj
import OwnerOrderMine from '../views/owner/OwnerOrderMine.vue'//hws、zj
import OwnerWallet from '../views/owner/OwnerWallet.vue'//yzr
import OwnerFeedback from '../views/owner/OwnerFeedback.vue'//yzr
//管理员
import AdminLogin from '../views/admin/AdminLogin.vue'//wyx
import AdminUsers from '../views/admin/AdminUsers.vue'//wyx
import AdminOrders from '../views/admin/AdminOrders.vue'//hws、zj
import AdminVehicles from '../views/admin/AdminVehicles.vue'//zj
import AdminFeedback from '../views/admin/AdminFeedback.vue'//yzr

function getSession() {
  try {
    //‘session’键里保存的是当前登录用户的完整信息（包括token登录令牌、角色、认证状态等）
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    //不存在则返回空对象
    return {}
  }
}

function isOwnerVerified(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') {
    return ['1', 'true', 'yes', 'y', 'on'].includes(value.trim().toLowerCase())
  }
  return Boolean(value)
}

//路由定义数组
const routes = [
  {
    //访问根路径‘/’时，自动跳转到‘/passenger/home’（乘客页面）
    path: '/',
    redirect: '/passenger/home'
  },
  //component的值是组件对象（即import的.vue文件）
  {
    path: '/login',
    component: LoginPage,
    meta: { public: true }//true代表无需登录即可访问的界面
  },
  {
    path: '/register',
    component: RegisterPage,
    meta: { public: true }//true代表无需登录即可访问的界面
  },
  {
    path: '/admin/login',
    component: AdminLogin,
    meta: { public: true, adminLogin: true }//true代表无需登录即可访问的界面，adminLogin--用于区分普通用户登录和管理员登录的界面
  },
  {
    path: '/403',
    component: ForbiddenPage,
    meta: { public: true }//true代表无需登录即可访问的界面
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      //requiresAuth--需要登录才能访问；role--则指定了可以访问的角色身份
      { path: 'passenger/home', component: PassengerHome, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/publish', component: PassengerOrderPublish, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/search', component: PassengerOrderSearch, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/mine', component: PassengerOrderMine, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/:id', component: PassengerOrderDetail, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/payment/:orderId', component: PassengerPayment, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/feedback', component: PassengerFeedback, meta: { requiresAuth: true, role: 'passenger' } },

      { path: 'me/profile', component: MeProfile, meta: { requiresAuth: true, role: 'user' } },
      { path: 'me/driver-application', component: MeDriverApplication, meta: { requiresAuth: true, role: 'user' } },
      { path: 'me/vehicles/create', component: OwnerVehicleForm, meta: { requiresAuth: true, role: 'user', ownerRequired: true } },
      { path: 'me/vehicles/:vehicleId/edit', component: OwnerVehicleForm, meta: { requiresAuth: true, role: 'user', ownerRequired: true } },
      { path: 'me/vehicles/:vehicleId/verify', component: OwnerVehicleVerify, meta: { requiresAuth: true, role: 'user', ownerRequired: true } },
      { path: 'me/vehicles', component: OwnerVehicles, meta: { requiresAuth: true, role: 'user', ownerRequired: true } },
      { path: 'me/messages', component: MeMessages, meta: { requiresAuth: true, role: 'user' } },
      { path: 'me/feedback', component: MeFeedback, meta: { requiresAuth: true, role: 'user' } },
      { path: 'me/security', component: MeSecurity, meta: { requiresAuth: true, role: 'user' } },
      { path: 'users/:userId', component: UserProfile, meta: { requiresAuth: true, role: 'user' } },

      { path: 'driver/home', component: OwnerHome, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/vehicles/create', redirect: '/me/vehicles/create' },
      { path: 'driver/vehicles/:vehicleId/edit', redirect: to => `/me/vehicles/${to.params.vehicleId}/edit` },
      { path: 'driver/vehicles/:vehicleId/verify', redirect: to => `/me/vehicles/${to.params.vehicleId}/verify` },
      { path: 'driver/vehicles', redirect: '/me/vehicles' },
      { path: 'driver/orders/available', component: OwnerOrderAvailable, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/orders/mine', component: OwnerOrderMine, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/orders/:id', component: PassengerOrderDetail, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/wallet', component: OwnerWallet, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/feedback', component: OwnerFeedback, meta: { requiresAuth: true, role: 'driver' } },

      { path: 'admin/users', component: AdminUsers, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/orders', component: AdminOrders, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/vehicle-verifications', component: AdminVehicles, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/vehicles', redirect: '/admin/vehicle-verifications' },
      { path: 'admin/feedback', component: AdminFeedback, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/driver-applications', component: AdminUsers, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/withdrawals', component: AdminFeedback, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/stats', component: AdminOrders, meta: { requiresAuth: true, role: 'admin' } },

      //这里就是owner和driver都可以定向到driver，这样的目的是语义上的双重身份：车辆的owner，乘客的driver（虽然不是非必需的）
      { path: 'owner/home', redirect: '/driver/home' },
      { path: 'owner/certification', redirect: '/me/driver-application' },
      { path: 'owner/vehicles/create', redirect: '/me/vehicles/create' },
      { path: 'owner/vehicles/:vehicleId/edit', redirect: to => `/me/vehicles/${to.params.vehicleId}/edit` },
      { path: 'owner/vehicles/:vehicleId/verify', redirect: to => `/me/vehicles/${to.params.vehicleId}/verify` },
      { path: 'owner/vehicles', redirect: '/me/vehicles' },
      { path: 'owner/orders/available', redirect: '/driver/orders/available' },
      { path: 'owner/orders/mine', redirect: '/driver/orders/mine' },
      { path: 'owner/wallet', redirect: '/driver/wallet' },
      { path: 'owner/feedback', redirect: '/driver/feedback' }
    ]
  },
  {
    //未定义的路径，显示“页面未找到”
    path: '/:pathMatch(.*)*',
    component: NotFoundPage,
    meta: { public: true }
  }
]

//创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

//这个函数会在每次路由跳转之前执行，用于权限校验。
router.beforeEach((to) => {
  const session = getSession()
  const isPublic = Boolean(to.meta.public)

  if (isPublic) {
    return true
  }

  if (!session.token) {
    return '/login'
  }

  if (to.meta.ownerRequired && !isOwnerVerified(session.ownerVerified) && session.role !== 'admin') {
    return '/me/driver-application'
  }

  const routeRole = to.meta.role
  if (!routeRole) {
    return true
  }

  if (routeRole === 'passenger') {
    return true
  }

  if (routeRole === 'user') {
    return true
  }

  if (routeRole === 'driver') {
    if (isOwnerVerified(session.ownerVerified) || session.role === 'admin') {
      return true
    }
    return '/403'
  }

  if (routeRole === 'admin') {
    if (session.role === 'admin') {
      return true
    }
    return '/403'
  }

  return true
})
export default router
