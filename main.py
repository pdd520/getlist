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

def build_search_url():
    """构建专用的CCTV搜索URL"""
    base_url = "https://tonkiang.us/"
    # 使用你提供的有效搜索参数
    search_params = "?iptv=CCTV&l=bfa258635a"
    return f"{base_url}{search_params}"

def fetch_cctv_streams():
    """使用专用搜索URL抓取直播源"""
    shanghai_time = get_shanghai_time()
    print(f"当前上海时间: {shanghai_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        url = build_search_url()
        print(f"请求专用搜索URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 调试：保存网页内容
        debug_file = f"debug_{shanghai_time.strftime('%Y%m%d_%H%M%S')}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"已保存网页内容到 {debug_file}")

        soup = BeautifulSoup(response.text, 'html.parser')
        streams = []
        
        # 针对搜索结果页面的特定抓取逻辑
        # 方法1：查找结果表格中的链接
        for row in soup.select('div.row'):
            if 'CCTV' in row.get_text().upper():
                # 查找流媒体链接
                stream_link = row.find('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I))
                if stream_link:
                    # 获取频道名称（取第一个非链接文本）
                    channel_name = next((text for text in row.stripped_strings if not text.startswith('http')), "CCTV频道")
                    streams.append({
                        'channel': channel_name,
                        'url': stream_link['href']
                    })
        
        # 方法2：直接搜索所有符合条件的链接
        if not streams:
            print("方法1未找到，尝试方法2...")
            for a in soup.find_all('a', href=re.compile(r'\.m3u8|\.flv|\.ts|rtmp:|rtsp:', re.I)):
                parent_text = a.find_parent().get_text().upper()
                if 'CCTV' in parent_text:
                    streams.append({
                        'channel': ' '.join(a.find_parent().stripped_strings),
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
        f.write(f"# 共找到 {len(streams)} 个CCTV直播源\n")
        f.write("# 格式: 频道,链接\n\n")
        
        for stream in streams:
            # 清理频道名称中的多余空格和换行
            clean_channel = ' '.join(stream['channel'].split())
            f.write(f"{clean_channel},{stream['url']}\n")
    
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
