<template>
  <div class="user-profile-page">
    <section class="page-card">
      <div class="eyebrow">用户资料</div>
      <h2>用户 {{ userId }}</h2>
      <p>这里用于从订单详情、接单车主、发单乘客入口查看对方资料。</p>
      <div class="actions">
        <van-button type="primary" block @click="openMessage">联系对方</van-button>
        <van-button plain type="warning" block to="/me/feedback">投诉 / 反馈</van-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const userId = computed(() => route.params.userId)

function openMessage() {
  router.push(`/me/messages?userId=${encodeURIComponent(userId.value)}`)
}
</script>

<style scoped>
.user-profile-page { display: grid; gap: 12px; }
.eyebrow { color: #165dff; font-size: 12px; font-weight: 700; margin-bottom: 4px; }
h2 { margin: 0 0 8px; color: #172033; }
p { margin: 0; color: #65758b; font-size: 13px; line-height: 1.6; }
.actions { display: grid; gap: 8px; margin-top: 16px; }
</style>
