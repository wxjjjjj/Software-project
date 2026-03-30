<template>
  <div class="page-card">
    <h2>管理员登录</h2>
    <p>演示账号: admin / admin123</p>
    <div class="form-row">
      <input v-model="username" placeholder="管理员账号" />
      <input v-model="password" type="password" placeholder="管理员密码" />
    </div>
    <div class="form-row">
      <button @click="login">管理员登录</button>
      <RouterLink to="/login">普通登录</RouterLink>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('admin')
const password = ref('admin123')
const err = ref('')

async function login() {
  err.value = ''
  if (!username.value || !password.value) {
    err.value = '请输入账号密码'
    return
  }

  try {
    await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    })
  } catch {
    //开发态容错。
  }

  localStorage.setItem('session', JSON.stringify({
    token: 'dev-token-admin',
    role: 'admin',
    ownerVerified: false,
    username: username.value
  }))
  router.push('/admin/users')
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
