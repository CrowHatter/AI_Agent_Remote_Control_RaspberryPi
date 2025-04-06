<!-- src/ChatHistory.vue -->
<template>
  <div>
    <h5>歷史聊天室</h5>
    <ul class="list-group">
      <li
        v-for="(chat, index) in chatHistories"
        :key="index"
        class="list-group-item chat-item"
        :class="{
          'bg-primary text-white': currentChatIndex === index,
          'bg-dark text-white': currentChatIndex !== index
        }"
        @click="$emit('switch-chat', index)"
      >
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

<style scoped>
.chat-item {
  cursor: pointer;
  transition: background-color 0.3s;
}

.chat-item:hover {
  background-color: #555 !important;
}
</style>
