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
      <!-- 右側：聊天視窗，僅包含 ChatWindow 組件，由該組件自行生成完整結構 -->
      <div :style="{ width: (100 - historyWidth) + '%' }" class="chat-window">
        <ChatWindow
          v-model="userInput"
          :chatMessages="currentChatMessages"
          @send-message="sendMessage"
          @execute-message="executeMessage"
        />
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
      historyWidth: 15,
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
    currentChatMessages() {
      return this.chatHistories[this.currentChatIndex].messages;
    },
    currentChatId() {
      return this.chatHistories[this.currentChatIndex].chat_id;
    }
  },
  mounted() {
    this.loadChatHistory(this.chatHistories[this.currentChatIndex].chat_id, this.currentChatIndex);
  },
  methods: {
    sendMessage() {
      if (!this.userInput.trim()) return;
      const userMsg = this.userInput;
      // 將使用者訊息加入對話記錄
      this.chatHistories[this.currentChatIndex].messages.push({
        sender: 'user',
        content: userMsg
      });
      const chatId = this.currentChatId;
      this.userInput = '';
      axios.post("http://localhost:5000/assistant1/chat", {
        chat_id: chatId,
        user_message: userMsg
      })
      .then(response => {
        console.log("Assistant1 API success:", response.data);
        const assistantMarkdown = response.data.assistant_markdown;
        // 將 Assistant 回覆轉成 HTML 後顯示，同時保留原始 markdown
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: marked.parse(assistantMarkdown),
          originalMarkdown: assistantMarkdown,
          executing: false
        });
      })
      .catch(error => {
        console.error("Assistant1 API error:", error);
        this.chatHistories[this.currentChatIndex].messages.push({
          sender: 'assistant',
          content: marked.parse("**Error:** 無法取得回覆，請稍後再試。")
        });
      });
    },
    loadChatHistory(chat_id, index) {
      axios.get(`http://localhost:5000/assistant1/history/${chat_id}`)
      .then(response => {
        const rawHistory = response.data.history || [];
        // 過濾 system 訊息，並根據 role 轉換格式
        const filteredMessages = rawHistory
          .filter(msg => msg.role !== 'system')
          .map(msg => {
            if (msg.role === 'assistant') {
              return {
                sender: 'assistant',
                content: marked.parse(msg.content),
                originalMarkdown: msg.content,
                executing: false
              }
            } else {
              return {
                sender: 'user',
                content: msg.content
              }
            }
          });
        this.chatHistories[index].messages = filteredMessages;
      })
      .catch(error => {
        console.error("Failed to load chat history:", error);
      });
    },
    executeMessage(messageIndex) {
      const message = this.currentChatMessages[messageIndex];
      if (!(message.sender === 'assistant' && message.originalMarkdown && message.originalMarkdown.includes('```'))) return;
      // 直接設定屬性，不用 Vue2 的 this.$set
      message.executing = true;
      const chatId = this.currentChatId;
      const formData = new FormData();
      formData.append("chat_id", chatId);
      formData.append("device_id", "Device1");
      // 傳送原始 markdown 給後端
      formData.append("markdown_content", message.originalMarkdown);
      
      axios.post("http://127.0.0.1:5000/assistant2/execute", formData)
      .then(response => {
        console.log("Assistant2 execute response:", response.data);
        // 不直接覆蓋 messages，而是重新刷新聊天室歷史以確保訊息格式正確
        this.loadChatHistory(chatId, this.currentChatIndex);
      })
      .catch(error => {
        console.error("Assistant2 execute error:", error);
      })
      .finally(() => {
        message.executing = false;
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
    switchChat(index) {
      this.currentChatIndex = index;
      const chat_id = this.chatHistories[index].chat_id;
      this.loadChatHistory(chat_id, index);
    }
  }
}
</script>

<style>
.chat-history {
  background-color: #343a40;
  color: #fff;
  border-right: 1px solid #555;
}

.divider {
  width: 5px;
  background-color: #555;
  cursor: ew-resize;
}
</style>
