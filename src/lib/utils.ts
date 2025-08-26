import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number | string | undefined | null): string {
  if (num === undefined || num === null) {
    return '0'
  }
  
  const n = typeof num === 'string' ? parseInt(num) || 0 : num
  
  if (isNaN(n)) {
    return '0'
  }
  
  if (n >= 10000) {
    return (n / 10000).toFixed(1) + 'w'
  }
  if (n >= 1000) {
    return (n / 1000).toFixed(1) + 'k'
  }
  return n.toString()
}

export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) {
    return '未知时间'
  }
  
  const date = new Date(dateString)
  
  if (isNaN(date.getTime())) {
    return '未知时间'
  }
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

export function truncateText(text: string | undefined | null, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export function isValidXhsUrl(url: string): boolean {
  const patterns = [
    /^https?:\/\/www\.xiaohongshu\.com\/explore\/[a-zA-Z0-9]+/,
    /^https?:\/\/www\.xiaohongshu\.com\/discovery\/item\/[a-zA-Z0-9]+/,
    /^https?:\/\/xhslink\.com\/[a-zA-Z0-9]+/
  ]
  
  return patterns.some(pattern => pattern.test(url))
}