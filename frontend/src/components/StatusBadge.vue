<script setup>
defineProps({ status: String, expired: Boolean, low: Boolean, negative: Boolean })
</script>
<template>
  <span class="badge" :class="expired ? 'danger' : negative ? 'danger' : low ? 'warning' : status === '良好' ? 'success' : 'neutral'">
    {{ expired ? '已过期' : negative ? '欠料' : low ? '低库存' : (status || '未知') }}
  </span>
</template>
