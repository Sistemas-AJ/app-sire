<template>
  <div class="bg-dark-lighter rounded-lg p-6 border border-dark-border">
    <h3 class="text-xs font-bold text-text-muted uppercase tracking-wider mb-2">{{ title }}</h3>
    <div class="flex items-end items-baseline">
      <span class="text-3xl font-bold text-white">{{ value }}</span>
      <span v-if="subValue" class="ml-2 text-sm" :class="subValueClass">{{ subValue }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  subValue: {
    type: String,
    default: ''
  },
  subValueClass: {
    type: String,
    default: 'text-text-muted'
  }
})
</script>
