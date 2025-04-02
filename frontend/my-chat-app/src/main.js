// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.min.css'

// 引入 marked 與 highlight.js
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css' // 可根據需要調整樣式

// 自訂 marked 的 renderer
const renderer = new marked.Renderer();
renderer.code = function (code, language) {
    const lang = language || '';
    // 確保 code 為字串
    const safeCode = typeof code === 'string' ? code : JSON.stringify(code);
    let highlighted;
    if (lang && hljs.getLanguage(lang)) {
        highlighted = hljs.highlight(safeCode, { language: lang }).value;
    } else {
        highlighted = hljs.highlightAuto(safeCode).value;
    }

    return (
        '<div class="code-block-container" style="position: relative; margin: 1em 0; background-color: #2d2d2d; border-radius: 5px;">' +
        '<div class="code-block-header" style="display: flex; justify-content: space-between; align-items: center; padding: 5px 10px; background-color: #1e1e1e; border-top-left-radius: 5px; border-top-right-radius: 5px;">' +
        '<span class="code-language" style="font-size: 0.9em; color: #fff;">' + lang.toUpperCase() + '</span>' +
        '<button class="copy-code-button" style="font-size: 0.8em; padding: 2px 5px; background-color: #007bff; color: #fff; border: none; border-radius: 3px; cursor: pointer;" onclick="copyCode(this)">Copy</button>' +
        '</div>' +
        '<pre style="margin: 0; overflow-x: auto; padding: 10px;"><code class="hljs ' + lang + '">' + highlighted + '</code></pre>' +
        '</div>'
    );
};

// 設定 marked 選項
marked.setOptions({
    renderer,
    highlight: function (code, language) {
        if (language && hljs.getLanguage(language)) {
            return hljs.highlight(code, { language }).value;
        }
        return code;
    }
});

// 全域複製函式，供複製按鈕使用
window.copyCode = function (button) {
    const pre = button.parentElement.nextElementSibling;
    if (pre) {
        const code = pre.innerText;
        navigator.clipboard.writeText(code).then(() => {
            button.innerText = 'Copied!';
            setTimeout(() => {
                button.innerText = 'Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy code: ', err);
        });
    }
};

createApp(App).mount('#app')
