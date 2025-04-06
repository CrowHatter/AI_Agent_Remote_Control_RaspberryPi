// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.min.css'

import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

// 自訂 marked 的 renderer
const renderer = new marked.Renderer();

// （保持你原本的 code block 渲染邏輯）
renderer.code = function (maybeCode, maybeLanguage) {
  let code = maybeCode;
  let lang = maybeLanguage || '';

  if (typeof code === 'object' && code !== null) {
    if (code.lang) {
      lang = code.lang;
    }
    if (typeof code.text === 'string') {
      code = code.text;
    } else {
      code = JSON.stringify(code);
    }
  }

  const safeCode = typeof code === 'string' ? code : String(code);

  let highlighted;
  if (lang && hljs.getLanguage(lang)) {
    highlighted = hljs.highlight(safeCode, { language: lang }).value;
  } else {
    highlighted = hljs.highlightAuto(safeCode).value;
  }

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

/**
 * 修正後的 copyCode：只複製同一個 code-block-container 裡的程式碼。
 */
window.copyCode = function (button) {
  // button.parentElement => code-block-header
  // button.parentElement.parentElement => code-block-container
  const codeBlockContainer = button.parentElement.parentElement;
  // 在同一個 code-block-container 中找 <pre> 元素
  const preElement = codeBlockContainer.querySelector('pre');
  
  if (preElement) {
    // 加一行 \n 結尾, 若不需要可移除
    const code = preElement.innerText + '\n';
    navigator.clipboard.writeText(code)
      .then(() => {
        button.innerText = 'Copied!';
        setTimeout(() => {
          button.innerText = 'Copy';
        }, 5000);
      })
      .catch(err => {
        console.error('Failed to copy code: ', err);
      });
  } else {
    console.warn('No <pre> element found in code-block-container.');
  }
};

// 建立並掛載 Vue App
createApp(App).mount('#app')
