import { marked } from 'marked'

/**
 * 将 Markdown 文本转为 HTML
 * @param {string} text - Markdown 文本
 * @returns {string} HTML 字符串
 */
export function renderMarkdown(text) {
  return marked.parse(text || '')
}
