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
      // 為每個聊天室增加 chat_id 屬性
      chatHistories: [
        { title: '聊天室 1', chat_id: 'chat1', messages: [] },
        { title: '聊天室 2', chat_id: 'chat2', messages: [] }
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
  mounted() {
    // 初次載入時，取得預設聊天室的歷史記錄
    this.loadChatHistory(this.chatHistories[this.currentChatIndex].chat_id, this.currentChatIndex);
  },
  methods: {
    // 送出訊息後，呼叫後端 API，並將使用者與 Assistant 的回覆加入對話記錄
    sendMessage() {
      if (!this.userInput.trim()) return;
      const userMsg = this.userInput;

      // 1. 將使用者訊息加入對話記錄（靠右顯示）
      this.chatHistories[this.currentChatIndex].messages.push({
        sender: 'user',
        content: userMsg
      });

      // 2. 清空輸入框
      this.userInput = '';

      // 3. 呼叫後端 API
      const chatId = this.chatHistories[this.currentChatIndex].chat_id;
      axios.post("http://localhost:5000/assistant1/chat", {
        chat_id: chatId,
        user_message: userMsg
      })
      .then(response => {
        console.log("API call success:", response.data);
        // 將 Assistant 回覆先以 marked 轉成 HTML
        const assistantMarkdown = response.data.assistant_markdown;
        const parsedReply = marked.parse(assistantMarkdown);

        // 4. 將 Assistant 的回覆加入對話記錄（靠左顯示）
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: parsedReply
        });
      })
      .catch(error => {
        console.error("API call error:", error);
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: marked.parse("**Error:** 無法取得回覆，請稍後再試。")
        });
      });
    },

    // 根據 chat_id 載入聊天室歷史記錄
    loadChatHistory(chat_id, index) {
      axios.get(`http://localhost:5000/assistant1/history/${chat_id}`)
      .then(response => {
        // 從後端取得的 history，過濾掉 system 並做前端格式轉換
        const rawHistory = response.data.history || [];
        const filteredMessages = rawHistory
          .filter(msg => msg.role !== 'system')
          .map(msg => {
            if (msg.role === 'assistant') {
              return {
                sender: 'assistant',
                content: marked.parse(msg.content)
              }
            } else {
              // 預設當作 user
              return {
                sender: 'user',
                content: msg.content
              }
            }
          });

        // Vue 3 直接賦值即可
        this.chatHistories[index].messages = filteredMessages;
      })
      .catch(error => {
        console.error("Failed to load chat history:", error);
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

    // 切換聊天室：更新 currentChatIndex 並載入該聊天室歷史記錄
    switchChat(index) {
      this.currentChatIndex = index;
      const chat_id = this.chatHistories[index].chat_id;
      this.loadChatHistory(chat_id, index);
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
