<template>
  <div class="publish-page">
    <van-form @submit="onSubmit">

      <!-- ── 路线 ── -->
      <div class="form-section">
        <div class="fs-header">
          <span class="fs-dot"></span>行程路线
        </div>
        <div class="route-inputs">
          <div class="ri-row">
            <span class="ri-icon start">●</span>
            <div class="loc-wrap">
              <van-field
                v-model="form.start_loc"
                placeholder="出发地"
                required clearable
                :rules="[{ required: true, message: '请填写出发地' }]"
                @input="filterSug('start')"
                @blur="() => setTimeout(() => showStart = false, 150)"
                @focus="filterSug('start')"
                class="ri-field"
              />
              <div v-show="showStart && sugStart.length" class="loc-suggestions">
                <div
                  v-for="s in sugStart" :key="s"
                  class="loc-suggestion-item"
                  @mousedown.prevent="pickSug('start', s)"
                >{{ s }}</div>
              </div>
            </div>
          </div>
          <div class="ri-connector">
            <span class="ri-vline"></span>
          </div>
          <div class="ri-row">
            <span class="ri-icon end">●</span>
            <div class="loc-wrap">
              <van-field
                v-model="form.end_loc"
                placeholder="目的地"
                required clearable
                :rules="[{ required: true, message: '请填写目的地' }]"
                @input="filterSug('end')"
                @blur="() => setTimeout(() => showEnd = false, 150)"
                @focus="filterSug('end')"
                class="ri-field"
              />
              <div v-show="showEnd && sugEnd.length" class="loc-suggestions">
                <div
                  v-for="s in sugEnd" :key="s"
                  class="loc-suggestion-item"
                  @mousedown.prevent="pickSug('end', s)"
                >{{ s }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 时间 ── -->
      <div class="form-section">
        <div class="fs-header">
          <span class="fs-dot"></span>出发时间窗口
        </div>
        <van-cell-group inset>
          <van-field
            v-model="form.depart_time_from"
            label="最早出发"
            type="datetime-local"
            required
            :rules="[{ required: true, message: '请选择出发时间' }]"
          />
          <van-field
            v-model="form.depart_time_to"
            label="最晚出发"
            type="datetime-local"
            required
            :rules="[{ required: true, message: '请选择最晚时间' }]"
          />
        </van-cell-group>
      </div>

      <!-- ── 拼车设置 ── -->
      <div class="form-section">
        <div class="fs-header">
          <span class="fs-dot"></span>拼车设置
        </div>
        <van-cell-group inset>
          <van-field
            v-model.number="form.group_size"
            label="我方人数"
            type="digit"
            placeholder="含本人共几位"
            required
            :rules="[{ required: true }]"
          ><template #extra><span class="field-hint">人</span></template></van-field>
          <van-field
            v-model.number="form.extra_seats"
            label="还能带几人"
            type="digit"
            placeholder="0 表示不带其他人"
          ><template #extra><span class="field-hint">人</span></template></van-field>

          <!-- 座位预览 -->
          <div class="seat-preview">
            <div class="sp-item sp-total">
              <div class="sp-val">{{ totalSeats }}</div>
              <div class="sp-key">共占座位</div>
            </div>
            <template v-if="perPerson">
              <div class="sp-sep"></div>
              <div class="sp-item sp-price">
                <div class="sp-val">¥{{ perPerson }}</div>
                <div class="sp-key">每人均价</div>
              </div>
            </template>
          </div>

          <van-field
            v-model="form.expected_price"
            label="预期总价"
            type="number"
            placeholder="例：45.00"
            required
            :rules="[{ required: true }]"
          ><template #extra><span class="field-hint">¥</span></template></van-field>
        </van-cell-group>
      </div>

      <!-- ── 标签 ── -->
      <div class="form-section">
        <div class="fs-header">
          <span class="fs-dot"></span>个性标签
        </div>
        <div class="tag-panel">
          <div class="tag-cloud">
            <span
              v-for="t in AVAILABLE_TAGS" :key="t"
              class="tag-chip"
              :class="{ active: selectedTags.includes(t) }"
              @click="toggleTag(t)"
            >{{ t }}</span>
            <span
              v-for="t in customTags" :key="'c-'+t"
              class="tag-chip custom active"
            >{{ t }}<span class="tag-chip-close" @click.stop="removeCustomTag(t)">×</span></span>
          </div>
          <div class="custom-tag-row">
            <input
              v-model="newTag"
              placeholder="自定义标签，回车添加"
              class="custom-input"
              @keyup.enter="addCustomTag"
            />
            <button type="button" class="custom-add-btn" @click="addCustomTag">＋</button>
          </div>
        </div>
      </div>

      <!-- ── 提交 ── -->
      <div class="submit-wrap">
        <van-button
          round block type="primary" size="large"
          native-type="submit"
          :loading="submitting"
          loading-text="发布中…"
          class="submit-btn"
        >发布订单</van-button>
      </div>

    </van-form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { rideApi, AVAILABLE_TAGS, LOCATION_SUGGESTIONS, calcPerPersonPrice } from '@/api/ride.js'

const router     = useRouter()
const submitting = ref(false)
const newTag     = ref('')
const customTags   = ref([])
const selectedTags = ref([])
const showStart = ref(false)
const showEnd   = ref(false)
const sugStart  = ref([])
const sugEnd    = ref([])

const form = ref({
  start_loc: '', end_loc: '',
  depart_time_from: '', depart_time_to: '',
  group_size: 1, extra_seats: 0, expected_price: '',
})

const totalSeats = computed(() => (form.value.group_size || 1) + (form.value.extra_seats || 0))
const perPerson  = computed(() => calcPerPersonPrice(form.value.expected_price, form.value.group_size, form.value.extra_seats))

function filterSug(field) {
  const kw = (field === 'start' ? form.value.start_loc : form.value.end_loc).toLowerCase()
  const filtered = kw
    ? LOCATION_SUGGESTIONS.filter(s => s.toLowerCase().includes(kw))
    : LOCATION_SUGGESTIONS.slice(0, 6)
  if (field === 'start') { sugStart.value = filtered; showStart.value = true }
  else { sugEnd.value = filtered; showEnd.value = true }
}

function pickSug(field, val) {
  if (field === 'start') { form.value.start_loc = val; showStart.value = false }
  else { form.value.end_loc = val; showEnd.value = false }
}

function toggleTag(t) {
  const idx = selectedTags.value.indexOf(t)
  if (idx >= 0) selectedTags.value.splice(idx, 1)
  else selectedTags.value.push(t)
}

function addCustomTag() {
  const tag = newTag.value.trim()
  if (!tag) return
  if (selectedTags.value.includes(tag) || customTags.value.includes(tag)) {
    showToast('标签已存在'); return
  }
  customTags.value.push(tag)
  newTag.value = ''
}

function removeCustomTag(tag) {
  customTags.value = customTags.value.filter(t => t !== tag)
}

async function onSubmit() {
  if (form.value.depart_time_from >= form.value.depart_time_to) {
    showToast('最晚出发时间必须晚于最早时间'); return
  }
  submitting.value = true
  try {
    await rideApi.publishOrder({
      ...form.value,
      expected_price: Number(form.value.expected_price),
      tags: [...selectedTags.value, ...customTags.value],
    })
    showSuccessToast('发布成功！')
    router.push('/passenger/orders/mine')
  } catch (e) {
    showToast(e.message || '发布失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.publish-page { padding-bottom: 32px; }

/* ── 区块 ── */
.form-section { margin-bottom: 10px; }
.fs-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  padding: 12px 4px 8px; letter-spacing: .3px;
}
.fs-dot { width: 8px; height: 8px; border-radius: 50%; background: #165DFF; flex-shrink: 0; }

/* ── 路线输入 ── */
.route-inputs {
  background: #fff; border-radius: 16px;
  padding: 6px 16px 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
}
.ri-row {
  display: flex; align-items: center; gap: 10px;
}
.ri-icon {
  font-size: 11px; flex-shrink: 0; line-height: 1;
}
.ri-icon.start { color: #165DFF; }
.ri-icon.end   { color: #f97316; }
.ri-field { padding: 10px 0; flex: 1; --van-cell-horizontal-padding: 0; }
.ri-connector { padding: 2px 0 2px 5px; }
.ri-vline {
  display: block; width: 1.5px; height: 18px;
  background: repeating-linear-gradient(180deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
  margin-left: 2px;
}

/* ── 座位预览 ── */
.seat-preview {
  display: flex; align-items: center;
  margin: 4px 16px 4px; padding: 10px 16px;
  background: #f8faff; border-radius: 10px;
  border: 1px solid #dce8ff;
}
.sp-item { flex: 1; text-align: center; }
.sp-sep  { width: 1px; height: 32px; background: #dce8ff; }
.sp-val  { font-size: 20px; font-weight: 800; color: #165DFF; line-height: 1; margin-bottom: 3px; }
.sp-price .sp-val { color: #f97316; }
.sp-key  { font-size: 11px; color: #94a3b8; }
.field-hint { color: #94a3b8; font-size: 13px; }

/* ── 标签 ── */
.tag-panel {
  background: #fff; border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
}
.tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.custom-tag-row { display: flex; align-items: center; gap: 8px; }
.custom-input {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 20px;
  padding: 6px 14px; font-size: 13px; outline: none; color: #1e293b;
  transition: border-color .15s;
}
.custom-input:focus { border-color: #165DFF; }
.custom-add-btn {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1.5px solid #165DFF; background: transparent;
  color: #165DFF; font-size: 18px; line-height: 28px;
  text-align: center; cursor: pointer; flex-shrink: 0;
  transition: all .15s;
}
.custom-add-btn:hover { background: #165DFF; color: #fff; }

/* ── 提交 ── */
.submit-wrap { padding: 20px 0 8px; }
.submit-btn  { box-shadow: 0 6px 20px rgba(22,93,255,.35) !important; }
</style>
