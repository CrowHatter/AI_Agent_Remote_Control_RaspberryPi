<!-- src/components/ChatHistory.vue -->
<template>
  <div>
    <h5>歷史聊天室</h5>
    <ul class="list-group">
      <li v-for="(chat, index) in chatHistories" :key="index" class="list-group-item"
        :class="{ 'bg-primary text-white': currentChatIndex === index, 'bg-dark text-white': currentChatIndex !== index }"
        @click="$emit('switch-chat', index)">
        {{ chat.title }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'ChatHistory',
  props: {
    chatHistories: {
      type: Array,
      default: () => []
    },
    currentChatIndex: {
      type: Number,
      default: 0
    }
  }
}
</script>
