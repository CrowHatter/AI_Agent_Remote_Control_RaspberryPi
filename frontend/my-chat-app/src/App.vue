<!-- src/App.vue -->
<template>
  <div class="container-fluid p-0">
    <div class="d-flex" style="height: 100vh;">
      <!-- 左側：歷史聊天室區 -->
      <div :style="{ width: historyWidth + '%' }" class="chat-history p-2" ref="historyPanel">
        <ChatHistory
          :chatHistories="chatHistories"
          :currentChatIndex="currentChatIndex"
          @switch-chat="switchChat" />
      </div>
      <!-- 分隔線：可拖曳 -->
      <div class="divider" @mousedown="startDrag"></div>
      <!-- 右側：聊天視窗 -->
      <div :style="{ width: (100 - historyWidth) + '%' }" class="chat-window d-flex flex-column">
        <ChatWindow
          :chatMessages="currentChatMessages"
          v-model="userInput"
          @send-message="sendMessage" />
      </div>
    </div>
  </div>
</template>

<script>
import ChatHistory from './components/ChatHistory.vue'
import ChatWindow from './components/ChatWindow.vue'
import axios from 'axios'
import { marked } from 'marked'

export default {
  name: 'App',
  components: { ChatHistory, ChatWindow },
  data() {
    return {
      historyWidth: 15, // 左側佔 15%
      chatHistories: [
        { title: '聊天室 1', messages: [] },
        { title: '聊天室 2', messages: [] }
      ],
      currentChatIndex: 0,
      userInput: '',
      isDragging: false
    }
  },
  computed: {
    // 傳入目前選擇聊天室的訊息記錄
    currentChatMessages() {
      return this.chatHistories[this.currentChatIndex].messages;
    }
  },
  methods: {
    // 送出訊息後，呼叫後端 API，並將使用者與 LLM 回覆加入對話記錄
    sendMessage() {
      if (!this.userInput.trim()) return;
      const userMsg = this.userInput;

      // 將使用者訊息加入對話記錄
      this.chatHistories[this.currentChatIndex].messages.push({
        sender: 'user',
        content: userMsg
      });

      // 清空輸入框
      this.userInput = '';

      // 呼叫後端 API
      axios.post("http://localhost:5000/assistant1/chat", {
        chat_id: "chat1",
        user_message: userMsg
      })
      .then(response => {
        // 可以先檢查回傳資料
        console.log("API call success:", response.data);

        // 取得後端回傳的 assistant_markdown
        const assistantMarkdown = response.data.assistant_markdown;

        // 將 Markdown 轉成 HTML
        const parsedReply = marked.parse(assistantMarkdown);

        // 將 Assistant 回覆加入對話記錄
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: parsedReply
        });
      })
      .catch(error => {
        console.error("API call error:", error);
        // 若 API 發生錯誤，加入錯誤訊息
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: marked.parse("**Error:** 無法取得回覆，請稍後再試。")
        });
      });
    },
    startDrag() {
      this.isDragging = true;
      document.addEventListener('mousemove', this.onDrag);
      document.addEventListener('mouseup', this.stopDrag);
    },
    onDrag(e) {
      if (!this.isDragging) return;
      const containerWidth = this.$el.clientWidth;
      let newWidth = (e.clientX / containerWidth) * 100;
      if (newWidth < 10) newWidth = 10;
      if (newWidth > 50) newWidth = 50;
      this.historyWidth = newWidth;
    },
    stopDrag() {
      this.isDragging = false;
      document.removeEventListener('mousemove', this.onDrag);
      document.removeEventListener('mouseup', this.stopDrag);
    },
    // 切換聊天室
    switchChat(index) {
      this.currentChatIndex = index;
    }
  }
}
</script>

<style scoped>
/* 深色模式背景 */
.chat-history,
.chat-window {
  background-color: #343a40;
  color: #fff;
}

/* 左側聊天室邊框 */
.chat-history {
  border-right: 1px solid #555;
}

/* 分隔線 */
.divider {
  width: 5px;
  background-color: #555;
  cursor: ew-resize;
}
</style>
