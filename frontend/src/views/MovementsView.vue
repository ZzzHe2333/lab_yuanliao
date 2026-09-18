<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const route = useRoute()
const chemicals = ref([])
const rows = ref([])
const error = ref('')
const saving = ref(false)
const filters = reactive({ search: '', chemical_id: '', movement_type: '' })
const form = reactive({
  chemical_id: '',
  movement_type: 'out',
  quantity: null,
  operator: '',
  purpose: '',
  reference_no: '',
  notes: ''
})

const selected = computed(() => chemicals.value.find(c => String(c.id) === String(form.chemical_id)))
const movementMeta = {
  in: { label: '入库', hint: '采购到货、拿样入库或补充库存', sign: '+', className: 'move-in' },
  out: { label: '领用', hint: '实验、小试、中试或样品制作领用', sign: '-', className: 'move-out' },
  return: { label: '退库', hint: '未使用完原料退回仓库', sign: '+', className: 'move-return' }
}

function fmtTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').replace('Z', '').slice(0, 19)
}

async function loadChemicals() {
  chemicals.value = await api.chemicals({ sort: 'name', order: 'asc' })
}

async function loadRows() {
  try {
    rows.value = await api.movements(filters)
    error.value = ''
  } catch (e) {
    error.value = e.message
  }
}

async function submit() {
  if (!form.chemical_id || !form.quantity || Number(form.quantity) <= 0) {
    error.value = '请选择原料并填写大于 0 的数量'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await api.createMovement({
      ...form,
      chemical_id: Number(form.chemical_id),
      quantity: Number(form.quantity)
    })
    const keepChemical = form.chemical_id
    const keepOperator = form.operator
    Object.assign(form, {
      chemical_id: keepChemical,
      movement_type: form.movement_type,
      quantity: null,
      operator: keepOperator,
      purpose: '',
      reference_no: '',
      notes: ''
    })
    await loadChemicals()
    await loadRows()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

watch(filters, loadRows, { deep: true })

onMounted(async () => {
  await loadChemicals()
  const qid = route.query.chemical_id
  if (qid) {
    form.chemical_id = String(qid)
    filters.chemical_id = String(qid)
  }
  await loadRows()
})
</script>

<template>
  <PageHeader title="库存流水" subtitle="所有入库、领用和退库都在这里形成可追溯记录" />

  <div v-if="error" class="alert danger-box">{{ error }}</div>

  <div class="movement-layout">
    <form class="panel movement-form" @submit.prevent="submit">
      <div class="panel-title">
        <div>
          <h2>登记库存变动</h2>
          <p>保存后自动更新当前库存</p>
        </div>
      </div>

      <div class="movement-type-grid">
        <button
          v-for="(meta, key) in movementMeta"
          :key="key"
          type="button"
          class="movement-type-btn"
          :class="[meta.className, { selected: form.movement_type === key }]"
          @click="form.movement_type = key"
        >
          <b>{{ meta.label }}</b>
          <small>{{ meta.hint }}</small>
        </button>
      </div>

      <label class="field-label">
        原料 *
        <select v-model="form.chemical_id" class="input" required>
          <option value="">请选择原料</option>
          <option v-for="c in chemicals" :key="c.id" :value="String(c.id)">
            {{ c.name }} · {{ c.quantity }} {{ c.unit }} · {{ c.warehouse_name || '未分仓' }}
          </option>
        </select>
      </label>

      <div v-if="selected" class="stock-preview">
        <div>
          <span>当前库存</span>
          <b>{{ selected.quantity }} {{ selected.unit }}</b>
        </div>
        <div>
          <span>本次操作后</span>
          <b>
            {{ form.quantity
              ? (form.movement_type === 'out'
                  ? Math.max(0, Number(selected.quantity) - Number(form.quantity || 0))
                  : Number(selected.quantity) + Number(form.quantity || 0))
              : selected.quantity }}
            {{ selected.unit }}
          </b>
        </div>
      </div>

      <div class="form-grid compact-grid">
        <label>
          数量 *
          <div class="quantity-input-wrap">
            <input v-model.number="form.quantity" type="number" min="0.000001" step="0.001" class="input" required />
            <span>{{ selected?.unit || '单位' }}</span>
          </div>
        </label>
        <label>
          经办人
          <input v-model="form.operator" class="input" placeholder="例如：付钰航" />
        </label>
        <label class="span-2">
          用途 / 项目
          <input v-model="form.purpose" class="input" placeholder="例如：03J 小试、样品制作、补充库存" />
        </label>
        <label>
          单据号 / 关联编号
          <input v-model="form.reference_no" class="input" placeholder="可留空" />
        </label>
        <label>
          备注
          <input v-model="form.notes" class="input" placeholder="可留空" />
        </label>
      </div>

      <button class="btn primary movement-submit" :disabled="saving || !form.chemical_id">
        {{ saving ? '保存中...' : `确认${movementMeta[form.movement_type].label}` }}
      </button>
    </form>

    <section class="panel movement-ledger">
      <div class="panel-title">
        <div>
          <h2>库存流水</h2>
          <p>最近 {{ rows.length }} 条记录</p>
        </div>
      </div>

      <div class="filter-panel movement-filters">
        <input v-model="filters.search" class="input search" placeholder="搜索原料 / 经办人 / 用途 / 单据号" />
        <select v-model="filters.chemical_id" class="input">
          <option value="">全部原料</option>
          <option v-for="c in chemicals" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
        </select>
        <select v-model="filters.movement_type" class="input">
          <option value="">全部类型</option>
          <option value="in">入库</option>
          <option value="out">领用</option>
          <option value="return">退库</option>
        </select>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>原料</th>
              <th>类型</th>
              <th>变动</th>
              <th>库存变化</th>
              <th>用途 / 经办人</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in rows" :key="m.id">
              <td class="nowrap">{{ fmtTime(m.created_at) }}</td>
              <td>
                <RouterLink v-if="m.chemical_id" :to="`/chemicals/${m.chemical_id}`" class="strong-link">
                  {{ m.current_chemical_name || m.chemical_name }}
                </RouterLink>
                <span v-else>{{ m.chemical_name }}（已删除）</span>
                <small class="block">{{ m.reference_no || '无单据号' }}</small>
              </td>
              <td>
                <span class="movement-badge" :class="`type-${m.movement_type}`">{{ m.movement_label }}</span>
              </td>
              <td :class="m.movement_type === 'out' ? 'stock-minus' : 'stock-plus'">
                {{ m.movement_type === 'out' ? '-' : '+' }}{{ m.quantity }} {{ m.unit }}
              </td>
              <td>{{ m.quantity_before }} → {{ m.quantity_after }} {{ m.unit }}</td>
              <td>
                {{ m.purpose || '-' }}
                <small class="block">{{ m.operator || '未填写经办人' }}<template v-if="m.notes"> · {{ m.notes }}</template></small>
              </td>
            </tr>
            <tr v-if="!rows.length"><td colspan="6" class="empty">暂无库存流水。</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
