
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager

def test_config():
    """测试配置加载"""
    config_manager = ConfigManager()
    
    print("测试配置加载...")
    print(f"下载延迟: {config_manager.app_config.download_delay}s")
    print(f"并发数: {config_manager.app_config.max_workers}")
    print(f"窗口宽度: {config_manager.app_config.window_width}")
    print(f"窗口高度: {config_manager.app_config.window_height}")
    
    # 检查配置文件
    if Path("app_config.json").exists():
        print("\napp_config.json 文件内容:")
        with open("app_config.json", "r", encoding="utf-8") as f:
            print(f.read())
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_config()
