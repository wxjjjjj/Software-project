<template>
  <div class="complaint-page">
    <section class="page-card complaint-card">
      <div class="eyebrow">投诉举报</div>
      <h2>提交投诉</h2>
      <p class="intro">
      </p>

      <div v-if="sourceOrderId" class="context-tip">已自动关联当前行程，无需重复填写行程信息。</div>

      <van-form class="complaint-form" @submit="handleSubmit">
        <van-field
          v-model.trim="form.defendantName"
          label="投诉用户名"
          placeholder="请输入要投诉的用户名"
          :rules="[{ required: true, message: '请填写投诉用户名' }]"
        />

        <div class="field-block">
          <div class="field-title">投诉类型</div>
          <div class="reason-grid">
            <button
              v-for="option in reasonOptions"
              :key="option.value"
              type="button"
              class="reason-chip"
              :class="{ active: form.reasonType === option.value }"
              @click="form.reasonType = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <van-field
          v-model.trim="form.detail"
          label="投诉详情"
          type="textarea"
          rows="4"
          autosize
          maxlength="800"
          show-word-limit
          placeholder="请描述发生了什么、你希望平台如何处理"
          :rules="[{ required: true, message: '请填写投诉详情' }]"
        />

        <van-button
          class="submit-btn"
          type="danger"
          block
          round
          native-type="submit"
          :loading="submitting"
        >
          提交投诉
        </van-button>
      </van-form>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { createComplaint, getUserId } from '../../api/ops.js'

const route = useRoute()
const submitting = ref(false)
const form = ref({ defendantName: '', reasonType: 1, detail: '' })

const reasonOptions = [
  { label: '行程纠纷', value: 1 },
  { label: '安全问题', value: 2 },
  { label: '费用问题', value: 3 },
  { label: '服务态度', value: 4 },
  { label: '其他', value: 0 },
]

const sourceOrderId = computed(() => String(route.query.orderId || '').trim())
const routeUsername = computed(() => String(route.query.username || route.query.targetUser || '').trim())
const selectedReason = computed(() =>
  reasonOptions.find((option) => option.value === form.value.reasonType) || reasonOptions[0]
)

watch(
  routeUsername,
  (value) => {
    if (value) form.value.defendantName = value
  },
  { immediate: true },
)

function numericUserId(value) {
  const text = String(value || '').trim()
  if (!/^\d+$/.test(text)) return null
  const parsed = Number(text)
  return Number.isSafeInteger(parsed) ? parsed : null
}

function buildDetail(name, detail) {
  return [
    `投诉用户名：${name}`,
    `投诉类型：${selectedReason.value.label}`,
    detail,
  ].join('\n')
}

async function handleSubmit() {
  const defendantName = form.value.defendantName.trim()
  const detail = form.value.detail.trim()
  if (!defendantName || !detail) return

  submitting.value = true
  try {
    await createComplaint({
      orderId: sourceOrderId.value || null,
      plaintiffId: getUserId(),
      defendantId: numericUserId(defendantName),
      reasonType: Number(form.value.reasonType) || 0,
      detail: buildDetail(defendantName, detail),
    })
    showToast('投诉已提交，管理员会尽快处理')
    form.value.detail = ''
    if (!routeUsername.value) form.value.defendantName = ''
  } catch (error) {
    showToast(error.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.complaint-page {
  display: grid;
  gap: 12px;
}

.complaint-card {
  padding: 18px 16px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 6px;
}

h2 {
  margin: 0;
  color: #172033;
  font-size: 22px;
}

.intro {
  margin: 8px 0 0;
  color: #65758b;
  font-size: 13px;
  line-height: 1.6;
}

.context-tip {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #eef5ff;
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
}

.complaint-form {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.field-block {
  padding: 12px;
  border: 1px solid #e4edff;
  border-radius: 14px;
  background: #fbfdff;
}

.field-title {
  margin-bottom: 10px;
  color: #334155;
  font-size: 14px;
  font-weight: 800;
}

.reason-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reason-chip {
  border: 1px solid #d7e5ff;
  border-radius: 999px;
  padding: 7px 12px;
  background: #fff;
  color: #52657d;
  font-size: 12px;
  font-weight: 700;
}

.reason-chip.active {
  border-color: #165dff;
  background: #165dff;
  color: #fff;
  box-shadow: 0 4px 12px rgba(22, 93, 255, .18);
}

.submit-btn {
  margin-top: 2px;
}

:deep(.van-field) {
  border: 1px solid #e4edff;
  border-radius: 14px;
  background: #fbfdff;
}

:deep(.van-field__label) {
  color: #334155;
  font-weight: 800;
}
</style>
