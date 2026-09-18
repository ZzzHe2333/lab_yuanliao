<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const c = ref(null)
const movements = ref([])
const error = ref('')

function fmtTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').replace('Z', '').slice(0, 19)
}

async function load() {
  try {
    c.value = await api.chemical(route.params.id)
    movements.value = await api.chemicalMovements(route.params.id, 10)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function delSds() {
  if (!confirm('删除该 SDS 文件？')) return
  try {
    await api.deleteSds(c.value.id)
    c.value.sds_filename = null
  } catch (e) {
    alert(e.message)
  }
}

function printLabel() {
  window.print()
}
</script>

<template>
  <PageHeader title="原料详情" subtitle="详细信息、库存、二维码、SDS 与库存变动历史">
    <RouterLink v-if="c" class="btn ghost no-print" :to="`/movements?chemical_id=${c.id}`">入库 / 领用 / 退库</RouterLink>
    <RouterLink v-if="c" class="btn primary no-print" :to="`/chemicals/${c.id}/edit`">编辑信息</RouterLink>
  </PageHeader>

  <div v-if="error" class="alert danger-box">{{ error }}</div>

  <section v-if="c" class="detail-grid">
    <div class="panel detail-main">
      <div class="chemical-hero">
        <div>
          <small>#{{ c.id }}</small>
          <h2>{{ c.name }}</h2>
          <p>CAS {{ c.cas || '未填写' }}</p>
        </div>
        <StatusBadge :status="c.status" :expired="c.is_expired" :low="c.is_low_stock" />
      </div>

      <div class="kv-grid">
        <div><span>库存数量</span><b>{{ c.quantity }} {{ c.unit }}</b></div>
        <div><span>低库存阈值</span><b>{{ c.low_stock_threshold || '-' }} {{ c.low_stock_threshold ? c.unit : '' }}</b></div>
        <div><span>采购日期</span><b>{{ c.purchase_date || '-' }}</b></div>
        <div><span>到期日期</span><b :class="{ red:c.is_expired }">{{ c.expiration_date || '-' }}</b></div>
        <div><span>仓库</span><b>{{ c.warehouse_name || '-' }}</b></div>
        <div><span>库位</span><b>{{ [c.room, c.cabinet && `柜 ${c.cabinet}`, c.shelf && `层 ${c.shelf}`].filter(Boolean).join(' / ') || '-' }}</b></div>
        <div><span>品牌</span><b>{{ c.brand || '-' }}</b></div>
        <div><span>批号</span><b>{{ c.batch_no || '-' }}</b></div>
        <div><span>供应商</span><b>{{ c.supplier || '-' }}</b></div>
        <div><span>储存条件</span><b>{{ c.storage_condition || '-' }}</b></div>
      </div>

      <div class="notes">
        <span>备注</span>
        <p>{{ c.notes || '无备注' }}</p>
      </div>
    </div>

    <aside class="panel qr-card">
      <h2>二维码标签</h2>
      <img :src="api.qrUrl(c.id)" :alt="`${c.name} QR`" />
      <p>LAB-YUANLIAO:{{ c.id }}</p>
      <button class="btn ghost no-print" @click="printLabel">打印标签</button>
      <a class="btn ghost no-print" :href="api.qrUrl(c.id)" download>下载二维码</a>
      <template v-if="c.sds_filename">
        <a class="btn primary no-print" :href="api.sdsUrl(c.id)" target="_blank">查看 SDS</a>
        <button class="btn danger-btn no-print" @click="delSds">删除 SDS</button>
      </template>
      <p v-else class="muted">尚未上传 SDS，可在编辑页面上传。</p>
    </aside>
  </section>

  <section v-if="c" class="panel detail-movements no-print">
    <div class="panel-title">
      <div>
        <h2>最近库存流水</h2>
        <p>展示最近 10 次入库、领用或退库</p>
      </div>
      <RouterLink :to="`/movements?chemical_id=${c.id}`">查看全部 →</RouterLink>
    </div>

    <div class="table-wrap">
      <table>
        <thead><tr><th>时间</th><th>类型</th><th>数量</th><th>库存变化</th><th>用途</th><th>经办人</th></tr></thead>
        <tbody>
          <tr v-for="m in movements" :key="m.id">
            <td class="nowrap">{{ fmtTime(m.created_at) }}</td>
            <td><span class="movement-badge" :class="`type-${m.movement_type}`">{{ m.movement_label }}</span></td>
            <td :class="m.movement_type === 'out' ? 'stock-minus' : 'stock-plus'">
              {{ m.movement_type === 'out' ? '-' : '+' }}{{ m.quantity }} {{ m.unit }}
            </td>
            <td>{{ m.quantity_before }} → {{ m.quantity_after }} {{ m.unit }}</td>
            <td>{{ m.purpose || '-' }}<small v-if="m.reference_no" class="block">单据：{{ m.reference_no }}</small></td>
            <td>{{ m.operator || '-' }}</td>
          </tr>
          <tr v-if="!movements.length"><td colspan="6" class="empty">暂无库存流水。</td></tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
