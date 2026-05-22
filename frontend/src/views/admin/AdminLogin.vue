<template>
  <div class="admin-login-page">
    <div class="login-card">
      <h2 style="color: #67c23a;">系统管理员登录</h2>
      <div class="form-item">
        <label>管理员账号</label>
        <input v-model="form.username" type="text" placeholder="Admin Username" />
      </div>
      <div class="form-item">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="Password" />
      </div>
      <button class="login-btn admin-btn" @click="handleAdminLogin" :disabled="loading">
        {{ loading ? '验证中...' : '进入管理系统' }}
      </button>
      <div class="footer-links">
        <router-link to="/login">返回普通用户登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const handleAdminLogin = async () => {
  if (!form.value.username || !form.value.password) {
    alert('请填写账号密码')
    return
  }

  loading.value = true
  try {
    // 【关键修改】：调用你在 account_domain.py 定义的 /api/admin/login
    const response = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })

    const data = await response.json()

    if (response.ok) {
      // 存储管理员 Session
      const sessionData = {
        userId: data.userId,
        username: data.username,
        role: 'admin',
        token: 'admin-token-' + data.userId
      }
      localStorage.setItem('session', JSON.stringify(sessionData))
      alert('管理员认证通过')
      router.push('/admin/users') // 跳转到用户管理页面
    } else {
      alert(data.detail || '管理员登录失败：权限不足或密码错误')
    }
  } catch (error) {
    alert('网络错误，请确保网关和后端服务已启动')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page { height: 100vh; display: flex; align-items: center; justify-content: center; background: #2c3e50; }
.login-card { background: white; padding: 40px; border-radius: 8px; width: 350px; }
.admin-btn { background: #67c23a !important; }
.form-item label { display: block; margin-bottom: 8px; font-weight: bold; }
.form-item input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
.login-btn { width: 100%; padding: 12px; border: none; border-radius: 4px; color: white; cursor: pointer; }
.footer-links { margin-top: 20px; text-align: center; font-size: 13px; }
</style>