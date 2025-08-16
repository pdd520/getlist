import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz
import os
import time

def get_shanghai_time():
    """获取上海时区的当前时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def fetch_with_retry(url, max_retries=3, delay=5):
    """带重试机制的请求函数"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"请求失败，第 {attempt + 1} 次重试... 错误: {str(e)}")
            time.sleep(delay)
    return None

def fetch_cctv_streams():
    """抓取CCTV直播源"""
    urls_to_try = [
        "https://tonkiang.us/?iptv=CCTV",
        "http://tonkiang.us/?iptv=CCTV",  # 尝试HTTP协议
        "https://tonkiang.us/hoteliptv.php?iptv=CCTV"  # 备用路径
    ]
    
    shanghai_time = get_shanghai_time()
    print(f"当前上海时间: {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for url in urls_to_try:
        print(f"\n尝试URL: {url}")
        try:
            response = fetch_with_retry(url)
            debug_file = f"debug_{shanghai_time.strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"成功获取页面内容，已保存到 {debug_file}")

            soup = BeautifulSoup(response.text, 'html.parser')
            streams = []
            
            # 方法1：查找表格中的频道
            for row in soup.select('div.row, tr'):
                if 'CCTV' in row.get_text().upper():
                    link = row.find('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I))
                    if link:
                        channel = re.sub(r'\s+', ' ', row.get_text()).strip()
                        streams.append({
                            'channel': channel[:100],  # 限制长度
                            'url': link['href']
                        })
            
            # 方法2：直接搜索所有链接
            if not streams:
                for a in soup.find_all('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I)):
                    if 'CCTV' in a.get_text().upper():
                        streams.append({
                            'channel': a.get_text().strip(),
                            'url': a['href']
                        })
            
            if streams:
                print(f"从 {url} 找到 {len(streams)} 个直播源")
                return streams
            
        except Exception as e:
            print(f"URL {url} 抓取失败: {str(e)}")
            continue
    
    print("所有URL尝试均失败")
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
