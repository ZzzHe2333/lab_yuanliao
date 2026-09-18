<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const warehouses = ref([])
const error = ref('')
const saving = ref(false)
const sds = ref(null)
const id = computed(() => route.params.id)
const editing = computed(() => Boolean(id.value))

const form = reactive({
  name: '',
  cas: '',
  purchase_date: '',
  expiration_date: '',
  status: '良好',
  quantity: 0,
  unit: 'g',
  low_stock_threshold: 0,
  warehouse_id: null,
  room: '',
  cabinet: '',
  shelf: '',
  supplier: '',
  brand: '',
  batch_no: '',
  storage_condition: '',
  notes: '',
  is_new_material: false
})

onMounted(async () => {
  warehouses.value = await api.warehouses()
  if (!form.warehouse_id && warehouses.value[0]) form.warehouse_id = warehouses.value[0].id
  if (editing.value) Object.assign(form, await api.chemical(id.value))
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form }
    if (editing.value) delete payload.quantity
    const item = editing.value
      ? await api.updateChemical(id.value, payload)
      : await api.createChemical(payload)
    if (sds.value) await api.uploadSds(item.id, sds.value)
    router.push(`/chemicals/${item.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <PageHeader
    :title="editing ? '编辑原料' : '新增原料'"
    :subtitle="editing ? '修改基础资料；库存数量请通过库存流水调整' : '登记原料基本信息、初始库存、位置与 SDS'"
  >
    <RouterLink v-if="editing" class="btn ghost" :to="`/movements?chemical_id=${id}`">库存操作</RouterLink>
  </PageHeader>

  <div v-if="error" class="alert danger-box">{{ error }}</div>

  <form class="panel form-panel" @submit.prevent="save">
    <div class="form-section">
      <h2>基本信息</h2>
      <div class="form-grid">
        <label class="span-2">原料名称 *
          <input v-model="form.name" class="input" required placeholder="例如：丙烯腈" />
        </label>
        <label>CAS 号
          <input v-model="form.cas" class="input" placeholder="107-13-1" />
        </label>
        <label>批号
          <input v-model="form.batch_no" class="input" />
        </label>
        <label>品牌
          <input v-model="form.brand" class="input" />
        </label>
        <label>供应商
          <input v-model="form.supplier" class="input" />
        </label>
        <label class="span-2 new-material-toggle">
          <input v-model="form.is_new_material" type="checkbox" />
          <span>
            <b>标记为新原料</b>
            <small>新原料领用时允许库存扣成负值，用于记录配方/实验已消耗但尚未补录入库的情况。</small>
          </span>
        </label>
      </div>
    </div>

    <div class="form-section">
      <h2>库存与状态</h2>
      <div v-if="editing" class="stock-edit-notice">
        <div>
          <span>当前库存</span>
          <b>{{ form.quantity }} {{ form.unit }}</b>
        </div>
        <p>库存数量不能在资料编辑页直接修改。请使用“入库 / 领用 / 退库”，系统会自动产生库存流水。</p>
        <RouterLink class="btn primary" :to="`/movements?chemical_id=${id}`">调整库存</RouterLink>
      </div>

      <div class="form-grid">
        <label v-if="!editing">初始库存
          <input v-model.number="form.quantity" type="number" min="0" step="0.001" class="input" />
          <small class="field-help">大于 0 时会自动生成一条“建档初始库存”入库流水。</small>
        </label>
        <label>单位
          <select v-model="form.unit" class="input" :disabled="editing && Number(form.quantity) !== 0">
            <option>g</option><option>kg</option><option>mL</option><option>L</option><option>瓶</option><option>桶</option><option>盒</option>
          </select>
          <small v-if="editing && Number(form.quantity) !== 0" class="field-help">库存归零后才能修改计量单位。</small>
        </label>
        <label>低库存预警
          <input v-model.number="form.low_stock_threshold" type="number" min="0" step="0.001" class="input" />
        </label>
        <label>状态
          <select v-model="form.status" class="input">
            <option>良好</option><option>一般</option><option>低库存</option><option>停用</option>
          </select>
        </label>
        <label>采购日期
          <input v-model="form.purchase_date" type="date" class="input" />
        </label>
        <label>到期日期
          <input v-model="form.expiration_date" type="date" class="input" />
        </label>
      </div>
    </div>

    <div class="form-section">
      <h2>存放位置</h2>
      <div class="form-grid">
        <label>仓库
          <select v-model="form.warehouse_id" class="input">
            <option :value="null">未指定</option>
            <option v-for="w in warehouses" :value="w.id" :key="w.id">{{ w.name }}</option>
          </select>
        </label>
        <label>房间 / 区域
          <input v-model="form.room" class="input" />
        </label>
        <label>柜号
          <input v-model="form.cabinet" class="input" />
        </label>
        <label>层号
          <input v-model="form.shelf" class="input" />
        </label>
        <label class="span-2">储存条件
          <input v-model="form.storage_condition" class="input" placeholder="例如：2-8℃、避光、通风" />
        </label>
      </div>
    </div>

    <div class="form-section">
      <h2>文件与备注</h2>
      <div class="form-grid">
        <label class="span-2">SDS 文件
          <input type="file" class="input file-input" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" @change="sds=$event.target.files[0]" />
        </label>
        <label class="span-2">备注
          <textarea v-model="form.notes" class="input textarea" rows="4"></textarea>
        </label>
      </div>
    </div>

    <div class="form-actions">
      <button type="button" class="btn ghost" @click="router.back()">取消</button>
      <button class="btn primary" :disabled="saving">{{ saving ? '保存中...' : '保存原料' }}</button>
    </div>
  </form>
</template>
