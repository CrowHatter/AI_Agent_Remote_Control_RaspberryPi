<!-- src/ChatWindow.vue -->
<template>
    <div class="chat-window-container">
        <!-- 聊天訊息區：位於輸入區上方，不與輸入區重疊 -->
        <div class="chat-messages" ref="chatMessages">
            <div v-for="(msg, index) in chatMessages" :key="index"
                :class="['chat-bubble', msg.sender === 'user' ? 'user-bubble' : 'assistant-bubble']">
                <template v-if="msg.sender === 'assistant'">
                    <div v-html="msg.content" v-highlight></div>
                </template>
                <template v-else>
                    <div>{{ msg.content }}</div>
                </template>
            </div>
        </div>
        <!-- 輸入區：位於下方，包含 textarea 與送信圖示按鈕 -->
        <div class="chat-input">
            <div class="input-container">
                <textarea class="form-control" placeholder="請輸入訊息..." v-model="inputValue" rows="1" @input="autoResize"
                    ref="autoText"></textarea>
                <button class="send-button" @click="handleSend">
                    ➤
                </button>
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
            this.$emit('update:modelValue', val)
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
            const maxHeight = window.innerHeight * 0.3; // 30% of viewport height
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

<style scoped>
/* 整個聊天視窗左右與下方 padding 5% */
.chat-window-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0 6% 2% 2%;
}

/* 聊天訊息區：填滿上方剩餘空間，可捲動 */
.chat-messages {
    flex-grow: 1;
    overflow-y: auto;
    margin-bottom: 10px;
}

/* 輸入區保持在下方 */
.chat-input {
    /* 輸入區內部自行排版 */
}

/* 輸入區內部容器，使用相對定位 */
.input-container {
    position: relative;
}

/* textarea：全寬，右側留空間給送信按鈕，最大高度限制為 30% viewport */
textarea.form-control {
    width: 100%;
    box-sizing: border-box;
    resize: none;
    padding-right: 50px;
    max-height: 30vh;
    overflow-y: auto;
}

/* 送信按鈕：絕對定位在右下角 */
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

/* 訊息氣泡樣式 */
.chat-bubble {
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    white-space: pre-wrap;
    overflow-wrap: break-word;
}

/* 使用者訊息：靠右顯示，寬度限制 60% */
.user-bubble {
    background-color: #007bff;
    max-width: 60%;
    margin-left: auto;
    text-align: left;
}

/* LLM 回覆：靠左顯示，寬度限制 80% */
.assistant-bubble {
    background-color: #6c757d;
    max-width: 80%;
    align-self: flex-start;
}
</style>
