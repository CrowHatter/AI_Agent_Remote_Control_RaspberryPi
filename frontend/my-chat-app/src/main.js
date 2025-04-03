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

// 修正重點：若 code 是物件 (含 type, text, lang...)，轉換為字串
renderer.code = function (maybeCode, maybeLanguage) {
  let code = maybeCode;
  let lang = maybeLanguage || '';

  // 若 code 為物件，嘗試取得真正的程式碼 (code.text) 與語言 (code.lang)
  if (typeof code === 'object' && code !== null) {
    if (code.lang) {
      lang = code.lang;
    }
    if (typeof code.text === 'string') {
      code = code.text;
    } else {
      // 如果沒有 text 屬性，就把整個物件序列化
      code = JSON.stringify(code);
    }
  }

  // 確保 code 為字串
  const safeCode = typeof code === 'string' ? code : String(code);

  // 語法高亮
  let highlighted;
  if (lang && hljs.getLanguage(lang)) {
    highlighted = hljs.highlight(safeCode, { language: lang }).value;
  } else {
    highlighted = hljs.highlightAuto(safeCode).value;
  }

  // 回傳自訂 HTML 模板
  return (
    '<div class="code-block-container" style="position: relative; margin: 1em 0; background-color: #2d2d2d; border-radius: 5px;">' +
    '<div class="code-block-header" style="display: flex; justify-content: space-between; align-items: center; padding: 5px 10px; background-color: #1e1e1e; border-top-left-radius: 5px; border-top-right-radius: 5px;">' +
    '<span class="code-language" style="font-size: 0.9em; color: #fff;">' + (lang.toUpperCase()) + '</span>' +
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
  // 依照上面模板結構，button 的父層是 header，再往下找 <pre> 區塊
  const pre = button.parentElement.parentElement.nextElementSibling;
  if (pre) {
    const code = pre.innerText;
    navigator.clipboard.writeText(code).then(() => {
      button.innerText = 'Copied!';
      setTimeout(() => {
        button.innerText = 'Copy';
      }, 5000);
    }).catch(err => {
      console.error('Failed to copy code: ', err);
    });
  }
};

createApp(App).mount('#app')
