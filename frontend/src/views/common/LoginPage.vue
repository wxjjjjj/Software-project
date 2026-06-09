<template>
  <div class="login-page">
    <div class="login-card">
      <h2>用户登录</h2>

      <div class="form-item">
        <label>用户名</label>
        <input v-model.trim="form.username" type="text" placeholder="请输入用户名" />
      </div>

      <div class="form-item">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" />
      </div>

      <button class="login-btn" :disabled="loading" @click="handleLogin">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="footer-links">
        <router-link to="/register">立即注册</router-link>
        <router-link to="/admin/login">管理员入口</router-link>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const form = ref({
  username: '',
  password: '',
})

async function handleLogin() {
  error.value = ''

  if (!form.value.username || !form.value.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })

    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      error.value = data.detail || '登录失败：账号或密码错误'
      return
    }

    const sessionData = {
      token: 'token-' + data.userId,
      role: data.role,
      userId: data.userId,
      username: data.username,
      ownerVerified: Boolean(data.driver && data.driver.status === 'approved'),
    }

    localStorage.setItem('session', JSON.stringify(sessionData))
    router.push(data.role === 'driver' ? '/driver/home' : '/passenger/home')
  } catch {
    error.value = '请求失败，请检查 8000 网关和 8001 后端是否启动'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(22, 93, 255, 0.12), transparent 28%),
    #f4f7fb;
}

.login-card {
  width: min(100%, 340px);
  padding: 28px 22px 22px;
  border: 1px solid #dce8ff;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(22, 93, 255, 0.08);
}

h2 {
  margin: 0 0 22px;
  text-align: center;
  color: #172033;
}

.form-item {
  margin-bottom: 14px;
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  color: #52657d;
  font-size: 13px;
}

.form-item input {
  width: 100%;
  border: 1px solid #d8e2f0;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.login-btn {
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 12px;
  background: #165dff;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.footer-links {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.footer-links a {
  color: #165dff;
  text-decoration: none;
}

.error-text {
  margin: 14px 0 0;
  color: #d14343;
  font-size: 13px;
}
</style>
