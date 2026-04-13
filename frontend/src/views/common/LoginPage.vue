<template>
  <div class="page-card">
    <h2>用户登录</h2>
    <p>默认登录为拼车人账号（开发态模拟）。</p>
    <div class="form-row">
      <input v-model="username" placeholder="用户名" />
      <input v-model="password" type="password" placeholder="密码" />
    </div>
    <div class="form-row">
      <button @click="login">登录</button>
      <RouterLink to="/register">去注册</RouterLink>
      <RouterLink to="/admin/login">管理员登录</RouterLink>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')

async function login() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  try {
    await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    })
  } catch {
    // 开发态即使后端未启动，也允许本地登录演示路由。
  }

  localStorage.setItem('session', JSON.stringify({
    token: 'dev-token-user',
    role: 'user',
    ownerVerified: false,
    username: username.value,
    userId: username.value,   // 供 ride 域等其他域用 X-User-Id 识别身份
  }))
  router.push('/passenger/home')
}
</script>

<style scoped>
.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

input {
  border: 1px solid #ced7e9;
  border-radius: 8px;
  padding: 8px 10px;
}

button {
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
}

.err {
  color: #d61f1f;
}
</style>
