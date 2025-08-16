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
    url = "https://tonkiang.us/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"{get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')} - 开始抓取直播源...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        streams = []
        
        # 查找包含CCTV的频道
        for item in soup.find_all('div', class_=re.compile('channel|stream|item')):
            title_elem = item.find(class_=re.compile('title|name'))
            if title_elem and 'CCTV' in title_elem.text.upper():
                stream_url = item.find('a', href=re.compile(r'\.m3u8|\.flv|rtmp|rtsp'))
                if stream_url:
                    streams.append({
                        'channel': title_elem.text.strip(),
                        'url': stream_url['href']
                    })
        
        print(f"找到 {len(streams)} 个CCTV直播源")
        return streams
    
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def save_to_file(streams):
    """将结果保存到CCTV.txt"""
    if not streams:
        print("没有找到可用的直播源，不生成文件")
        return
    
    with open('CCTV.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 抓取时间: {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 共找到 {len(streams)} 个CCTV直播源\n")
        f.write("# 格式: 频道,链接\n\n")
        
        for stream in streams:
            f.write(f"{stream['channel']},{stream['url']}\n")
    
    print("结果已保存到 CCTV.txt")

def git_push():
    """自动提交更新"""
    commit_message = f"自动更新CCTV直播源 {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}"
    os.system('git config --global user.name "GitHub Actions"')
    os.system('git config --global user.email "actions@github.com"')
    os.system('git add CCTV.txt')
    os.system(f'git commit -m "{commit_message}"')
    os.system('git push')

if __name__ == "__main__":
    now = get_shanghai_time()
    print(f"当前时间(Asia/Shanghai): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    cctv_streams = fetch_cctv_streams()
    save_to_file(cctv_streams)
    
    # 如果在GitHub Actions中运行，则自动提交
    if os.getenv('GITHUB_ACTIONS') == 'true':
        git_push()
