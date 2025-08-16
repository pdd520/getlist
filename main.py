import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz
import os

def get_shanghai_time():
    """获取上海时区的当前时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def fetch_cctv_streams():
    """抓取CCTV直播源"""
    url = "https://tonkiang.us/?iptv=CCTV"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        shanghai_time = get_shanghai_time()
        print(f"当前上海时间: {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        streams = []
        
        # 针对搜索结果页面的特定抓取逻辑
        for result in soup.select('div.resultplus'):
            # 提取频道名称
            channel_elem = result.select_one('div.channel div.tip')
            if not channel_elem:
                continue
                
            channel = channel_elem.get_text().strip()
            
            # 提取流媒体链接 - 查找包含链接的tba元素
            link_elem = result.select_one('tba.irya')
            if link_elem:
                url = link_elem.get_text().strip()
                if re.search(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', url, re.I):
                    streams.append({
                        'channel': channel,
                        'url': url
                    })
        
        # 去重
        unique_streams = []
        seen = set()
        for s in streams:
            ident = f"{s['channel']}_{s['url']}"
            if ident not in seen:
                seen.add(ident)
                unique_streams.append(s)
        
        print(f"找到 {len(unique_streams)} 个CCTV直播源")
        return unique_streams
    
    except Exception as e:
        print(f"抓取失败: {str(e)}")
        return []

def save_to_file(streams):
    """保存结果到文件"""
    if not streams:
        print("没有找到可用的直播源")
        # 创建空文件以便GitHub Actions可以提交
        with open('CCTV.txt', 'w', encoding='utf-8') as f:
            f.write("# 本次未找到可用直播源\n")
        return False
    
    with open('CCTV.txt', 'w', encoding='utf-8') as f:
        shanghai_time = get_shanghai_time()
        f.write(f"# 抓取时间(Asia/Shanghai): {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 共找到 {len(streams)} 个CCTV直播源\n")
        f.write("# 格式: 频道,链接\n\n")
        
        for stream in streams:
            clean_channel = re.sub(r'[\n\r\t]+', ' ', stream['channel']).strip()
            f.write(f"{clean_channel},{stream['url']}\n")
    
    print("结果已保存到 CCTV.txt")
    return True

if __name__ == "__main__":
    streams = fetch_cctv_streams()
    file_saved = save_to_file(streams)
    
    # 确保文件存在
    if not os.path.exists('CCTV.txt'):
        with open('CCTV.txt', 'w') as f:
            f.write("# 自动创建的空文件\n")

    # GitHub Actions 自动提交
    if os.getenv('GITHUB_ACTIONS') == 'true':
        try:
            os.system('git config --global user.name "GitHub Actions"')
            os.system('git config --global user.email "actions@github.com"')
            os.system('git add CCTV.txt debug_*.html')
            os.system('git commit -m "自动更新CCTV直播源" || echo "没有变化可提交"')
            os.system('git push')
        except Exception as e:
            print(f"Git提交出错: {str(e)}")
