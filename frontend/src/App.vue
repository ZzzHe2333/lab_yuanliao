<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
const route = useRoute()
const items = [
  ['/', '总览', '⌂'],
  ['/chemicals', '原料库存', '▦'],
  ['/chemicals/new', '新增原料', '+'],
  ['/scan', '扫码查询', '⌁'],
  ['/warehouses', '仓库管理', '▣']
]
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">JL</div>
        <div><strong>实验室原料</strong><small>Inventory</small></div>
      </div>
      <nav>
        <RouterLink v-for="[path, name, icon] in items" :key="path" :to="path" :class="{ active: route.path === path }">
          <span class="nav-icon">{{ icon }}</span><span>{{ name }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-foot">单账户 · 本地数据模式</div>
    </aside>
    <main class="main"><RouterView /></main>
  </div>
</template>
