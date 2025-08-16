import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz
import os

def get_shanghai_time():
    """获取准确的上海时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def should_fetch_previous_day():
    """判断是否需要抓取前一天的内容（凌晨0-6点）"""
    current_hour = get_shanghai_time().hour
    return current_hour < 6  # 早上6点前视为"前一天内容"

def build_url(target_date=None):
    """构建带日期的URL（如果网站支持）"""
    base_url = "https://tonkiang.us/"
    if target_date:
        # 如果网站支持日期参数，可以这样构建URL
        # 例如：https://tonkiang.us/?date=2025-08-16
        return f"{base_url}?date={target_date}"
    return base_url

def fetch_cctv_streams():
    """智能抓取直播源（自动处理凌晨时段）"""
    shanghai_time = get_shanghai_time()
    print(f"当前上海时间: {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 判断是否应该获取前一天的内容
    fetch_previous = should_fetch_previous_day()
    target_date = (shanghai_time - timedelta(days=1)).strftime('%Y-%m-%d') if fetch_previous else None
    
    if fetch_previous:
        print(f"凌晨时段({shanghai_time.hour}点)，尝试获取前一天({target_date})的内容...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        url = build_url(target_date)
        print(f"请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 调试：保存网页内容
        debug_file = f"debug_{shanghai_time.strftime('%Y%m%d_%H%M%S')}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"已保存网页内容到 {debug_file}")

        soup = BeautifulSoup(response.text, 'html.parser')
        streams = []
        
        # 方法1：查找包含CCTV的表格行或列表项
        for item in soup.select('tr, li, div.item'):
            text = item.get_text().upper()
            if 'CCTV' in text:
                links = item.find_all('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I))
                if links:
                    streams.append({
                        'channel': ' '.join(item.stripped_strings),
                        'url': links[0]['href']
                    })
        
        # 方法2：直接搜索所有流媒体链接
        if not streams:
            print("方法1未找到，尝试方法2...")
            for a in soup.find_all('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I)):
                if 'CCTV' in a.get_text().upper():
                    streams.append({
                        'channel': a.get_text().strip(),
                        'url': a['href']
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
        return False
    
    with open('CCTV.txt', 'w', encoding='utf-8') as f:
        shanghai_time = get_shanghai_time()
        f.write(f"# 抓取时间(Asia/Shanghai): {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if should_fetch_previous_day():
            f.write(f"# 注意：当前为凌晨时段，获取的是前一天内容\n")
        f.write(f"# 共找到 {len(streams)} 个CCTV直播源\n")
        f.write("# 格式: 频道,链接\n\n")
        
        for stream in streams:
            f.write(f"{stream['channel']},{stream['url']}\n")
    
    print("结果已保存到 CCTV.txt")
    return True

if __name__ == "__main__":
    streams = fetch_cctv_streams()
    file_saved = save_to_file(streams)
    
    # GitHub Actions 自动提交
    if file_saved and os.getenv('GITHUB_ACTIONS') == 'true':
        os.system('git config --global user.name "GitHub Actions"')
        os.system('git config --global user.email "actions@github.com"')
        os.system('git add CCTV.txt debug_*.html')
        os.system('git commit -m "自动更新CCTV直播源"')
        os.system('git push')
