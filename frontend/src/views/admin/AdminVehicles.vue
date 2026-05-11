<template>
  <div class="vehicle-review-page">
    <section class="page-card">
      <h2>管理员-车辆认证审核</h2>
      <p class="hint">查看车主提交的认证资料，并执行通过或驳回。</p>

      <van-tabs v-model:active="activeTab" @change="onTabChange">
        <van-tab title="待审核" name="pending" />
        <van-tab title="已通过" name="approved" />
        <van-tab title="已驳回" name="rejected" />
      </van-tabs>
    </section>

    <section class="page-card">
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="requests.length === 0" class="empty">当前筛选条件下暂无申请</div>

      <div class="request-list" v-else>
        <article class="request-item" v-for="item in requests" :key="item.id">
          <div class="row strong">申请 #{{ item.id }} · 车辆ID：{{ item.vehicle_id }}</div>
          <div class="row">车主用户：{{ item.owner_user_id }}</div>
          <div class="row">车主姓名：{{ item.owner_name }}</div>
          <div class="row">身份证号：{{ item.id_no_masked }}</div>
          <div class="row">驾驶证号：{{ item.driver_license_no }}</div>
          <div class="row">行驶证号：{{ item.vehicle_license_no }}</div>
          <div class="row">联系电话：{{ item.contact_phone || '-' }}</div>
          <div class="row">补充说明：{{ item.remark || '-' }}</div>
          <div class="row">提交时间：{{ item.created_at || '-' }}</div>
          <div class="row">当前状态：{{ statusText(item.status) }}</div>
          <div class="row" v-if="item.review_note">审核备注：{{ item.review_note }}</div>

          <template v-if="item.status === 'pending'">
            <van-field
              v-model.trim="reviewNoteMap[item.id]"
              :name="`note-${item.id}`"
              label="审核备注"
              placeholder="可填写驳回原因或补充说明"
            />
            <div class="actions">
              <van-button
                size="small"
                type="success"
                :loading="reviewingId === item.id"
                @click="review(item.id, 'approved')"
              >
                通过
              </van-button>
              <van-button
                size="small"
                type="danger"
                :loading="reviewingId === item.id"
                @click="review(item.id, 'rejected')"
              >
                驳回
              </van-button>
            </div>
          </template>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showNotify } from 'vant'
import { fetchVehicleVerifyRequests, reviewVehicleVerifyRequest } from '../../api/ride'

const activeTab = ref('pending')
const loading = ref(false)
const reviewingId = ref(null)
const requests = ref([])
const reviewNoteMap = ref({})

onMounted(() => {
  loadRequests(activeTab.value)
})

function statusText(status) {
  if (status === 'approved') {
    return '已通过'
  }
  if (status === 'rejected') {
    return '已驳回'
  }
  return '待审核'
}

async function onTabChange(name) {
  await loadRequests(String(name))
}

async function loadRequests(status) {
  loading.value = true
  try {
    const data = await fetchVehicleVerifyRequests(status)
    const items = Array.isArray(data.items)
      ? data.items.map((item) => ({
        ...item,
        id: item.id ?? item.request_id
      }))
      : []
    requests.value = items
    const noteMap = {}
    for (const item of items) {
      noteMap[item.id] = item.review_note || ''
    }
    reviewNoteMap.value = noteMap
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '认证申请加载失败' })
  } finally {
    loading.value = false
  }
}

async function review(requestId, decision) {
  if (reviewingId.value !== null) {
    return
  }

  reviewingId.value = requestId
  try {
    await reviewVehicleVerifyRequest(
      requestId,
      decision,
      reviewNoteMap.value[requestId] || ''
    )
    showNotify({ type: 'success', message: decision === 'approved' ? '审核通过' : '已驳回申请' })
    await loadRequests(activeTab.value)
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '审核失败' })
  } finally {
    reviewingId.value = null
  }
}
</script>

<style scoped>
.vehicle-review-page {
  display: grid;
  gap: 12px;
}

.hint {
  margin: 6px 0 12px;
  color: #5f6c80;
  font-size: 13px;
}

.request-list {
  display: grid;
  gap: 10px;
}

.request-item {
  border: 1px solid #e6edf7;
  border-radius: 8px;
  padding: 10px;
  background: #fbfcff;
}

.row {
  margin-top: 4px;
  color: #33425c;
  font-size: 13px;
}

.strong {
  margin-top: 0;
  font-weight: 600;
}

.actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.empty {
  padding: 8px 0;
  color: #6c7c93;
  font-size: 13px;
}
</style>
