
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, AppConfig
from downloader import Downloader

def test_download_delay():
    """测试下载延迟功能"""
    # 测试配置保存和加载
    config_manager = ConfigManager()
    
    print("测试应用配置...")
    print(f"当前下载延迟: {config_manager.app_config.download_delay}s")
    print(f"当前并发数: {config_manager.app_config.max_workers}")
    
    # 修改配置
    config_manager.app_config.download_delay = 1.0
    config_manager.app_config.max_workers = 1
    config_manager.save_app_config()
    print("配置已保存")
    
    # 重新加载
    config_manager2 = ConfigManager()
    print(f"重新加载后延迟: {config_manager2.app_config.download_delay}s")
    print(f"重新加载后并发数: {config_manager2.app_config.max_workers}")
    
    # 测试下载延迟
    print("\n测试下载延迟功能...")
    url = "https://www.xbqg8.net/176/176829/1.html"
    site_config = config_manager.get_site_by_url(url)
    
    if not site_config:
        print("未找到站点配置")
        return
    
    # 创建下载器，设置较短的延迟用于测试
    downloader = Downloader(site_config, max_workers=1, download_delay=0.5)
    
    # 测试多次下载的时间间隔
    start_times = []
    for i in range(3):
        start = time.time()
        html = downloader.fetch_url(url)
        end = time.time()
        start_times.append(start)
        
        if html:
            print(f"第{i+1}次下载成功，耗时: {end-start:.2f}s")
        else:
            print(f"第{i+1}次下载失败")
        
        # 计算间隔
        if i > 0:
            interval = start - start_times[i-1]
            print(f"  与上一次下载的间隔: {interval:.2f}s")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_download_delay()
