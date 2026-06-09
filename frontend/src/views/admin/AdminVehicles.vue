<template>
  <div class="vehicle-review-page">
    <section class="page-card page-hero">
      <div>
        <!-- <div class="eyebrow">车辆认证</div> -->
        <h2>车辆认证审核</h2>
        <!-- <p class="hint">查看车主提交的认证资料，并执行通过或驳回。</p> -->
      </div>

      <van-tabs v-model:active="activeTab" @change="onTabChange">
        <van-tab title="待审核" name="pending" />
        <van-tab title="已通过" name="approved" />
        <van-tab title="已驳回" name="rejected" />
      </van-tabs>
    </section>

    <section class="page-card">
      <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
      <van-empty v-else-if="requests.length === 0" description="当前筛选条件下暂无申请" />

      <div class="request-list" v-else>
        <article class="request-item" v-for="item in requests" :key="item.id">
          <div class="request-head">
            <div>
              <div class="request-title">申请 #{{ item.id }}</div>
              <div class="request-sub">车辆ID：{{ item.vehicle_id }}</div>
            </div>
            <span :class="['status-pill', item.status]">{{ statusText(item.status) }}</span>
          </div>
          <div class="info-grid">
            <div class="info-row"><span>车主用户</span><b>{{ item.owner_user_id }}</b></div>
            <div class="info-row"><span>车主姓名</span><b>{{ item.owner_name }}</b></div>
            <div class="info-row"><span>身份证号</span><b>{{ item.id_no_masked }}</b></div>
            <div class="info-row"><span>驾驶证号</span><b>{{ item.driver_license_no }}</b></div>
            <div class="info-row"><span>行驶证号</span><b>{{ item.vehicle_license_no }}</b></div>
            <div class="info-row"><span>联系电话</span><b>{{ item.contact_phone || '-' }}</b></div>
            <div class="info-row wide"><span>补充说明</span><b>{{ item.remark || '-' }}</b></div>
            <div class="info-row wide"><span>提交时间</span><b>{{ item.created_at || '-' }}</b></div>
            <div class="info-row wide" v-if="item.review_note"><span>审核备注</span><b>{{ item.review_note }}</b></div>
          </div>

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
  padding: 14px;
  padding-bottom: 28px;
}

.page-hero {
  display: grid;
  gap: 12px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.1;
  color: #172033;
}

.hint {
  margin: 8px 0 0;
  color: #52657d;
  font-size: 13px;
  line-height: 1.6;
}

.request-list {
  display: grid;
  gap: 10px;
}

.request-item {
  border: 1px solid #dce8ff;
  border-radius: 14px;
  padding: 14px;
  background: #fbfdff;
  box-shadow: 0 2px 12px rgba(22, 93, 255, .06);
}

.request-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #edf1f7;
}

.request-title {
  color: #172033;
  font-size: 15px;
  font-weight: 800;
}

.request-sub {
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
}

.status-pill {
  flex: 0 0 auto;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #dce8ff;
  background: #f0f5ff;
  color: #165dff;
  font-size: 12px;
  font-weight: 800;
}

.status-pill.approved {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #047857;
}

.status-pill.rejected {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  margin-bottom: 10px;
}

.info-row {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.info-row.wide {
  grid-column: 1 / -1;
}

.info-row span {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
}

.info-row b {
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

@media (max-width: 520px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
