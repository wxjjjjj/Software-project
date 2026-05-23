import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'

import LoginPage from '../views/common/LoginPage.vue'
import RegisterPage from '../views/common/RegisterPage.vue'
import NotFoundPage from '../views/common/NotFoundPage.vue'
import ForbiddenPage from '../views/common/ForbiddenPage.vue'
import UserProfile from '../views/common/UserProfile.vue'

import MeProfile from '../views/me/MeProfile.vue'
import MeDriverApplication from '../views/me/MeDriverApplication.vue'
import MeMessages from '../views/me/MeMessages.vue'
import MeFeedback from '../views/me/MeFeedback.vue'
import MeSecurity from '../views/me/MeSecurity.vue'

import PassengerHome from '../views/passenger/PassengerHome.vue'
import PassengerOrderPublish from '../views/passenger/PassengerOrderPublish.vue'
import PassengerOrderSearch from '../views/passenger/PassengerOrderSearch.vue'
import PassengerOrderDetail from '../views/passenger/PassengerOrderDetail.vue'
import PassengerOrderMine from '../views/passenger/PassengerOrderMine.vue'
import PassengerPayment from '../views/passenger/PassengerPayment.vue'
import PassengerFeedback from '../views/passenger/PassengerFeedback.vue'
import PassengerWallet from '../views/passenger/PassengerWallet.vue'
import ChatRoom from '../views/common/ChatRoom.vue'

import OwnerHome from '../views/owner/OwnerHome.vue'
import OwnerVehicles from '../views/owner/OwnerVehicles.vue'
import OwnerVehicleForm from '../views/owner/OwnerVehicleForm.vue'
import OwnerVehicleVerify from '../views/owner/OwnerVehicleVerify.vue'
import OwnerOrderAvailable from '../views/owner/OwnerOrderAvailable.vue'
import OwnerOrderMine from '../views/owner/OwnerOrderMine.vue'
import OwnerWallet from '../views/owner/OwnerWallet.vue'
import OwnerFeedback from '../views/owner/OwnerFeedback.vue'

import AdminLogin from '../views/admin/AdminLogin.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminOrders from '../views/admin/AdminOrders.vue'
import AdminVehicles from '../views/admin/AdminVehicles.vue'
import AdminFeedback from '../views/admin/AdminFeedback.vue'

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
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

const routes = [
  {
    path: '/',
    redirect: '/passenger/home',
  },
  {
    path: '/login',
    component: LoginPage,
    meta: { public: true },
  },
  {
    path: '/register',
    component: RegisterPage,
    meta: { public: true },
  },
  {
    path: '/admin/login',
    component: AdminLogin,
    meta: { public: true, adminLogin: true },
  },
  {
    path: '/403',
    component: ForbiddenPage,
    meta: { public: true },
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      { path: 'passenger/home', component: PassengerHome, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/publish', component: PassengerOrderPublish, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/search', component: PassengerOrderSearch, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/mine', component: PassengerOrderMine, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/orders/:id', component: PassengerOrderDetail, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/payment/:orderId', component: PassengerPayment, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/feedback', component: PassengerFeedback, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/wallet', component: PassengerWallet, meta: { requiresAuth: true, role: 'passenger' } },
      { path: 'passenger/chat/:orderId', component: ChatRoom, meta: { requiresAuth: true, role: 'passenger' } },

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
      { path: 'driver/certification', redirect: '/me/driver-application' },
      { path: 'driver/vehicles/create', redirect: '/me/vehicles/create' },
      { path: 'driver/vehicles/:vehicleId/edit', redirect: (to) => `/me/vehicles/${to.params.vehicleId}/edit` },
      { path: 'driver/vehicles/:vehicleId/verify', redirect: (to) => `/me/vehicles/${to.params.vehicleId}/verify` },
      { path: 'driver/vehicles', redirect: '/me/vehicles' },
      { path: 'driver/orders/available', component: OwnerOrderAvailable, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/orders/mine', component: OwnerOrderMine, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/orders/:id', component: PassengerOrderDetail, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/wallet', component: OwnerWallet, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/feedback', component: OwnerFeedback, meta: { requiresAuth: true, role: 'driver' } },
      { path: 'driver/chat/:orderId', component: ChatRoom, meta: { requiresAuth: true, role: 'driver' } },

      { path: 'admin/users', component: AdminUsers, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/orders', component: AdminOrders, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/vehicle-verifications', component: AdminVehicles, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/vehicles', redirect: '/admin/vehicle-verifications' },
      { path: 'admin/feedback', component: AdminFeedback, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/driver-applications', component: AdminUsers, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/withdrawals', component: AdminFeedback, meta: { requiresAuth: true, role: 'admin' } },
      { path: 'admin/stats', component: AdminOrders, meta: { requiresAuth: true, role: 'admin' } },

      { path: 'owner/home', redirect: '/driver/home' },
      { path: 'owner/certification', redirect: '/me/driver-application' },
      { path: 'owner/vehicles/create', redirect: '/me/vehicles/create' },
      { path: 'owner/vehicles/:vehicleId/edit', redirect: (to) => `/me/vehicles/${to.params.vehicleId}/edit` },
      { path: 'owner/vehicles/:vehicleId/verify', redirect: (to) => `/me/vehicles/${to.params.vehicleId}/verify` },
      { path: 'owner/vehicles', redirect: '/me/vehicles' },
      { path: 'owner/orders/available', redirect: '/driver/orders/available' },
      { path: 'owner/orders/mine', redirect: '/driver/orders/mine' },
      { path: 'owner/wallet', redirect: '/driver/wallet' },
      { path: 'owner/feedback', redirect: '/driver/feedback' },
      { path: 'owner/chat/:orderId', redirect: (to) => `/driver/chat/${to.params.orderId}` },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    component: NotFoundPage,
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const session = getSession()

  if (to.meta.public) {
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

  if (routeRole === 'passenger' || routeRole === 'user') {
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
