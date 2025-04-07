<template>
    <div class="chat-window-container">
      <!-- 聊天訊息區 -->
      <div class="chat-messages" ref="chatMessages">
        <div
          v-for="(msg, index) in chatMessages"
          :key="index"
          :class="['chat-bubble', msg.sender === 'assistant' ? 'assistant-bubble' : 'user-bubble']"
        >
          <!-- Assistant 訊息：使用 v-html 呈現已解析的 HTML -->
          <template v-if="msg.sender === 'assistant'">
            <div v-html="msg.content"></div>
          </template>
          <!-- User 訊息：直接呈現文字 -->
          <template v-else>
            <div>{{ msg.content }}</div>
          </template>
          <!-- 當 Assistant 的原始 Markdown 含有 code block 時顯示 Execute 按鈕 -->
          <button
            v-if="msg.sender === 'assistant' && msg.originalMarkdown && msg.originalMarkdown.includes('```')"
            class="execute-button"
            :class="{'executing': msg.executing}"
            :disabled="msg.executing"
            @click="$emit('execute-message', index)"
          >
            {{ msg.executing ? 'Executing' : 'Execute' }}
          </button>
        </div>
      </div>
  
      <!-- 輸入區：包含 textarea 與送信按鈕 -->
      <div class="chat-input">
        <div class="input-container">
          <textarea
            class="form-control"
            placeholder="請輸入訊息..."
            v-model="inputValue"
            rows="1"
            @input="autoResize"
            ref="autoText"
          ></textarea>
          <button class="send-button" @click="handleSend">➤</button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'ChatWindow',
    props: {
      chatMessages: {
        type: Array,
        default: () => []
      },
      modelValue: {
        type: String,
        default: ''
      }
    },
    data() {
      return {
        inputValue: this.modelValue
      }
    },
    watch: {
      inputValue(val) {
        this.$emit('update:modelValue', val);
      },
      modelValue(val) {
        if (val !== this.inputValue) {
          this.inputValue = val;
        }
      }
    },
    methods: {
      handleSend() {
        this.$emit('send-message');
        this.$nextTick(() => {
          const container = this.$refs.chatMessages;
          container.scrollTop = container.scrollHeight;
          this.resetTextareaHeight();
        });
      },
      autoResize(e) {
        const textarea = e.target;
        textarea.style.height = 'auto';
        const maxHeight = window.innerHeight * 0.3;
        if (textarea.scrollHeight < maxHeight) {
          textarea.style.height = textarea.scrollHeight + 'px';
          textarea.style.overflowY = 'hidden';
        } else {
          textarea.style.height = maxHeight + 'px';
          textarea.style.overflowY = 'auto';
        }
      },
      resetTextareaHeight() {
        const textarea = this.$refs.autoText;
        if (textarea) {
          textarea.style.height = 'auto';
        }
      }
    }
  }
  </script>
  
  <style>
  /* 不使用 scoped，確保樣式能夠全域生效 */
  .chat-window-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 2% 6% 2% 2%;
    background-color: #343a40;
    color: #fff;
    border-right: 1px solid #555;
  }
  
  .chat-messages {
    flex-grow: 1;
    overflow-y: auto;
    margin-bottom: 10px;
    position: relative;
  }
  
  .chat-input {
    /* 輸入區樣式，可根據需要調整 */
  }
  
  .input-container {
    position: relative;
  }
  
  textarea.form-control {
    width: 100%;
    box-sizing: border-box;
    resize: none;
    padding-right: 50px;
    max-height: 30vh;
    overflow-y: auto;
  }
  
  .send-button {
    position: absolute;
    bottom: 0px;
    right: 5px;
    background: none;
    border: none;
    font-size: 1.5em;
    color: #007bff;
    cursor: pointer;
  }
  
  .chat-bubble {
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    white-space: pre-wrap;
    overflow-wrap: break-word;
    position: relative;
  }
  
  .user-bubble {
    background-color: #007bff;
    max-width: 60%;
    margin-left: auto;
    text-align: left;
  }
  
  .assistant-bubble {
    background-color: #495057;
    align-self: flex-start;
    max-width: 80%;
  }
  
  .execute-button {
    position: absolute;
    right: 5px;
    bottom: 5px;
    background-color: #238636;
    color: #fff;
    border: none;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 0.8em;
    cursor: pointer;
  }
  
  .execute-button.executing {
    background-color: #f0ad4e;
  }
  </style>
  