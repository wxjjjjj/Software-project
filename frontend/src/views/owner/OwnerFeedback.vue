<template>
  <div class="page-card">
    <van-tabs v-model:active="tab">
      <van-tab title="提交投诉">
        <van-form @submit="handleSubmit">
          <van-field v-model="form.orderId" label="订单编号" placeholder="可选" />
          <van-field v-model="form.defendantId" label="对方用户ID" type="number" placeholder="可选" />
          <van-field v-model="form.reasonType" label="投诉类型" type="number" placeholder="0=其他 1=迟到 2=爽约 3=纠纷" />
          <van-field
            v-model="form.detail"
            label="投诉详情"
            type="textarea"
            rows="3"
            placeholder="请描述投诉内容"
            :rules="[{ required: true, message: '请填写投诉详情' }]"
          />
          <van-button type="danger" block native-type="submit" :loading="submitting">
            提交投诉
          </van-button>
        </van-form>
      </van-tab>

      <van-tab title="我的投诉">
        <van-list
          v-model:loading="listLoading"
          :finished="listFinished"
          finished-text="没有更多了"
          @load="loadList"
        >
          <van-cell
            v-for="item in list"
            :key="item.ticketId"
            :title="'投诉 #' + item.ticketId"
            :label="item.detail"
          >
            <template #value>
              <van-tag :type="statusTag(item.status)">{{ statusText(item.status) }}</van-tag>
            </template>
          </van-cell>
        </van-list>
        <van-empty v-if="!listLoading && list.length === 0" description="暂无投诉记录" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast } from 'vant'
import { createComplaint, listComplaints, getUserId } from '../../api/ops.js'

const tab = ref(0)
const submitting = ref(false)
const form = ref({ orderId: '', defendantId: '', reasonType: 0, detail: '' })
const list = ref([])
const listLoading = ref(false)
const listFinished = ref(false)
const listPage = ref(1)

const STATUS_MAP = { 0: '待处理', 1: '处理中', 2: '已解决', 3: '已驳回' }
const STATUS_TAG = { 0: 'warning', 1: 'primary', 2: 'success', 3: 'default' }

function statusText(s) { return STATUS_MAP[s] || '未知' }
function statusTag(s) { return STATUS_TAG[s] || 'default' }

async function handleSubmit() {
  submitting.value = true
  try {
    await createComplaint({
      orderId: form.value.orderId || null,
      plaintiffId: getUserId(),
      defendantId: form.value.defendantId ? parseInt(form.value.defendantId) : null,
      reasonType: parseInt(form.value.reasonType) || 0,
      detail: form.value.detail
    })
    showToast('投诉已提交')
    form.value = { orderId: '', defendantId: '', reasonType: 0, detail: '' }
  } catch (e) {
    showToast(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function loadList() {
  listLoading.value = true
  try {
    const data = await listComplaints(getUserId(), listPage.value)
    list.value.push(...data.items)
    listPage.value++
    if (list.value.length >= data.total) listFinished.value = true
  } catch {
    showToast('加载投诉记录失败')
  } finally {
    listLoading.value = false
  }
}
</script>
