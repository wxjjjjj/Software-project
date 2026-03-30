<template>
  <div class="page-card">
    <h2>用户注册</h2>
    <p>注册后默认是拼车人身份，可在个人中心认证车主。</p>
    <div class="form-row">
      <input v-model="username" placeholder="用户名" />
      <input v-model="password" type="password" placeholder="密码" />
    </div>
    <div class="form-row">
      <button @click="register">提交注册</button>
      <RouterLink to="/login">返回登录</RouterLink>
    </div>
    <p v-if="msg">{{ msg }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const msg = ref('')

async function register() {
  msg.value = ''
  if (!username.value || !password.value) {
    msg.value = '请填写完整信息'
    return
  }

  try {
    await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    })
  } catch {
    // 开发态允许无后端时继续演示。
  }

  msg.value = '注册成功，请返回登录'
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
</style>
