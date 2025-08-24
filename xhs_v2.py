import requests
import re
import json
from datetime import datetime
import os

class XHSCrawler:
  
  """精简版小红书爬虫类"""
  
  def __init__(self, cookies_str=None):
      """
      初始化爬虫
      Args:
          cookies_str: cookie字符串，如果为空则使用默认cookie
      """
      # 使用默认cookie，你可以根据需要更新
      default_cookie = ""
      
      self.cookies_str = cookies_str or default_cookie
      self.headers = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
          'Cookie': self.cookies_str,
          'Origin': 'https://www.xiaohongshu.com',
          'Referer': 'https://www.xiaohongshu.com',
          'Content-Type': 'application/json;charset=UTF-8'
      }
  
  @staticmethod
  def extract_xhs_url(text):
      """从文本中提取小红书链接"""
      try:
          # 匹配标准小红书链接
          pattern = r'https://www\.xiaohongshu\.com/\S+'
          match = re.search(pattern, text)
          if match:
              return match.group(0)
          
          # 匹配短链接
          short_pattern = r'http://xhslink\.com/\S+'
          short_match = re.search(short_pattern, text)
          if short_match:
              return short_match.group(0).rstrip('，,。.!！?？')
          
          return text  # 如果没有匹配到，直接返回原文本
      except Exception as e:
          print(f"提取链接时发生错误: {e}")
          return text
  
  @staticmethod
  def process_xhs_url(url):
      """从小红书链接中提取笔记id和xsec_token"""
      # 提取笔记ID
      note_id_pattern = r'/(?:item|explore)/([a-zA-Z0-9]+)'
      note_id_match = re.search(note_id_pattern, url)
      note_id = note_id_match.group(1) if note_id_match else None
      
      # 提取xsec_token
      token_pattern = r'xsec_token=([^&]+)'
      token_match = re.search(token_pattern, url)
      xsec_token = token_match.group(1) if token_match else ''
      
      # 构建标准URL
      if note_id:
          new_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_user"
      else:
          new_url = url
      
      return new_url, note_id, xsec_token
  
  @staticmethod
  def extract_initial_state(html_content):
      """从HTML响应中提取window.__INITIAL_STATE__的数据"""
      try:
          pattern = r"window\.__INITIAL_STATE__=({.*?})</script>"
          matches = re.search(pattern, html_content, re.DOTALL)
          
          if not matches:
              return None
              
          state = matches.group(1)
          
          # 替换JavaScript特有的语法
          state = state.replace("undefined", "null")
          state = state.replace("NaN", "null")
          state = state.replace("Infinity", "null")
          state = state.replace("-Infinity", "null")
          
          return json.loads(state)
      except Exception as e:
          print(f"提取数据失败: {str(e)}")
          return None
  
  @staticmethod
  def extract_note_details(note_info):
      """从笔记信息中提取详细数据"""
      if not note_info:
          return None
      
      # 提取基础信息
      note_details = {
          "note_id": note_info.get("noteId"),
          "type": note_info.get("type"),
          "title": note_info.get("title"),
          "desc": note_info.get("desc"),
          "time": note_info.get("time"),
          "ip_location": note_info.get("ipLocation"),
      }
      
      # 提取作者信息
      user = note_info.get("user", {})
      note_details["author"] = {
          "user_id": user.get("userId"),
          "nickname": user.get("nickname"),
          "avatar": user.get("avatar")
      }
      
      # 提取互动数据
      interact_info = note_info.get("interactInfo", {})
      note_details["interact"] = {
          "like_count": interact_info.get("likedCount", 0),
          "collect_count": interact_info.get("collectedCount", 0),
          "comment_count": interact_info.get("commentCount", 0),
          "share_count": interact_info.get("shareCount", 0)
      }
      
      # 提取标签信息
      tags = note_info.get("tagList", [])
      note_details["tags"] = [tag.get("name", "") for tag in tags if tag.get("name")]
      
      # 提取图片URL列表
      note_details["images"] = [
          img.get("urlDefault") for img in note_info.get("imageList", [])
          if img.get("urlDefault")
      ]
      
      # 提取视频信息
      video_urls = []
      if note_info.get("type") == "video":
          video = note_info.get("video", {})
          consumer = video.get("consumer", {})
          origin_video_key = consumer.get("originVideoKey") or consumer.get("origin_video_key")
          
          if origin_video_key:
              video_urls = [f"http://sns-video-bd.xhscdn.com/{origin_video_key}"]
      
      note_details["video_urls"] = video_urls
      
      return note_details

  def resolve_short_url(self, url):
      """解析小红书短链接"""
      try:
          response = requests.head(url, headers=self.headers, allow_redirects=True)
          return response.url
      except Exception as e:
          print(f"解析短链接失败: {str(e)}")
          return url

  def get_note_info(self, share_text):
      """
      获取笔记信息的主要方法
      Args:
          share_text: 包含小红书链接的分享文本
      Returns:
          dict: 包含笔记信息的字典
      """
      try:
          # 步骤1: 提取小红书链接
          xhs_url = self.extract_xhs_url(share_text)
          if not xhs_url:
              return {"error": "未找到有效的小红书链接"}
          
          # 步骤2: 处理短链接
          if "xhslink.com" in xhs_url:
              xhs_url = self.resolve_short_url(xhs_url)
          
          # 步骤3: 处理URL并构建新的URL
          new_url, note_id, xsec_token = self.process_xhs_url(xhs_url)
          
          # 步骤4: 请求笔记详情页面
          response = requests.get(new_url, headers=self.headers)
          
          if response.status_code != 200:
              return {"error": f"请求失败，状态码: {response.status_code}"}
          
          # 步骤5: 从页面中提取笔记数据
          initial_state = self.extract_initial_state(response.text)
          
          if not initial_state or "note" not in initial_state:
              return {"error": "无法从页面中提取笔记数据"}
          
          note_detail_map = initial_state["note"].get("noteDetailMap", {})
          if note_id not in note_detail_map:
              return {"error": f"未找到笔记ID {note_id} 的详细信息"}
          
          note_info = note_detail_map[note_id].get("note")
          note_details = self.extract_note_details(note_info)
          
          if not note_details:
              return {"error": "提取笔记详情失败"}
          
          return {
              "success": True,
              "note_id": note_id,
              "note_details": note_details,
              "original_url": xhs_url
          }
          
      except Exception as e:
          return {"error": f"处理过程中出现异常: {str(e)}"}

  def format_timestamp(self, timestamp):
      """格式化时间戳"""
      if not timestamp:
          return ''
      try:
          ts = int(timestamp)
          if ts > 10000000000:  # 毫秒级
              dt = datetime.fromtimestamp(ts / 1000)
          else:  # 秒级
              dt = datetime.fromtimestamp(ts)
          return dt.strftime('%Y-%m-%d %H:%M:%S')
      except:
          return str(timestamp)

# 简单的使用函数
def get_xiaohongshu_note(url, cookies=None):
  """
  简单的接口函数，供网页调用
  Args:
      url: 小红书链接
      cookies: 可选的cookie字符串
  Returns:
      dict: 笔记信息
  """
  crawler = XHSCrawler(cookies)
  result = crawler.get_note_info(url)
  
  if result.get("success"):
      note_details = result["note_details"]
      
      # 格式化返回数据
      formatted_result = {
          "success": True,
          "data": {
              "note_id": note_details["note_id"],
              "title": note_details["title"],
              "content": note_details["desc"],
              "type": "视频" if note_details["type"] == "video" else "图文",
              "author": {
                  "nickname": note_details["author"]["nickname"],
                  "user_id": note_details["author"]["user_id"],
                  "avatar": note_details["author"]["avatar"]
              },
              "stats": {
                  "likes": note_details["interact"]["like_count"],
                  "collects": note_details["interact"]["collect_count"],
                  "comments": note_details["interact"]["comment_count"],
                  "shares": note_details["interact"]["share_count"]
              },
              "publish_time": crawler.format_timestamp(note_details["time"]),
              "location": note_details["ip_location"],
              "tags": note_details["tags"],
              "images": note_details["images"],
              "videos": note_details["video_urls"]
          }
      }
      return formatted_result
  else:
      return {
          "success": False,
          "error": result.get("error", "未知错误")
      }

# 测试用例
if __name__ == "__main__":
  
  # 测试链接
  test_url = "https://www.xiaohongshu.com/discovery/item/6878b8950000000011002e20?source=webshare&xhsshare=pc_web&xsec_token=ABP3ErtPvtY6diVHCBrV3Y7YuuFuLWoDObdOUfTlz4U0k=&xsec_source=pc_share"
  
  result = get_xiaohongshu_note(test_url)
  
  print(json.dumps(result, ensure_ascii=False, indent=2))