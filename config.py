import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class SiteConfig:
    name: str
    domain: str
    catalog_container_xpath: Optional[str]
    catalog_start_marker: Optional[str]
    catalog_end_marker: Optional[str]
    catalog_next_page_xpath: Optional[str]
    content_xpath: Optional[str]
    content_start_marker: Optional[str]
    content_end_marker: Optional[str]
    ad_patterns: list[str]
    next_page_xpath: Optional[str]
    chapter_url_pattern: str
    download_delay: float


@dataclass
class ProxyConfig:
    enabled: bool
    proxy_type: str
    host: str
    port: int
    username: str
    password: str


@dataclass
class AppConfig:
    download_delay: float
    max_workers: int
    window_width: int
    window_height: int
    proxy: ProxyConfig


class ConfigManager:
    def __init__(self, config_path: str = "sites.json", app_config_path: str = "app_config.json"):
        self.config_path = Path(config_path)
        self.app_config_path = Path(app_config_path)
        self.sites: list[SiteConfig] = []
        self.app_config: Optional[AppConfig] = None
        self.load()
        self.load_app_config()

    def load(self) -> None:
        if not self.config_path.exists():
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}") from e
        self.sites = []
        for site in data.get("sites", []):
            try:
                config = SiteConfig(
                name=site["name"],
                domain=site["domain"],
                catalog_container_xpath=site.get("catalog", {}).get("container_xpath"),
                catalog_start_marker=site.get("catalog", {}).get("start_marker"),
                catalog_end_marker=site.get("catalog", {}).get("end_marker"),
                catalog_next_page_xpath=site.get("catalog", {}).get("next_page_xpath"),
                content_xpath=site.get("content", {}).get("content_xpath"),
                content_start_marker=site.get("content", {}).get("start_marker"),
                content_end_marker=site.get("content", {}).get("end_marker"),
                ad_patterns=site.get("content", {}).get("ad_patterns", []),
                next_page_xpath=site.get("content", {}).get("next_page_xpath"),
                chapter_url_pattern=site.get("chapter_url_pattern", ""),
                download_delay=site.get("download_delay", 1.0),
                )
            except KeyError as e:
                raise ValueError(f"站点配置缺少必需字段: {e}") from e
            self.sites.append(config)

    def load_app_config(self) -> None:
        if self.app_config_path.exists():
            try:
                with open(self.app_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                proxy_data = data.get("proxy", {})
                self.app_config = AppConfig(
                    download_delay=data["download_delay"],
                    max_workers=data["max_workers"],
                    window_width=data["window_width"],
                    window_height=data["window_height"],
                    proxy=ProxyConfig(
                        enabled=proxy_data.get("enabled", False),
                        proxy_type=proxy_data.get("type", "http"),
                        host=proxy_data.get("host", ""),
                        port=proxy_data.get("port", 8080),
                        username=proxy_data.get("username", ""),
                        password=proxy_data.get("password", "")
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"加载应用配置失败，使用默认值: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = {
            "download_delay": 1.0,
            "max_workers": 3,
            "window_width": 1200,
            "window_height": 700,
            "proxy": {
                "enabled": False,
                "type": "http",
                "host": "",
                "port": 8080,
                "username": "",
                "password": ""
            }
        }
        with open(self.app_config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        proxy_data = default_config["proxy"]
        self.app_config = AppConfig(
            download_delay=default_config["download_delay"],
            max_workers=default_config["max_workers"],
            window_width=default_config["window_width"],
            window_height=default_config["window_height"],
            proxy=ProxyConfig(
                enabled=proxy_data["enabled"],
                proxy_type=proxy_data["type"],
                host=proxy_data["host"],
                port=proxy_data["port"],
                username=proxy_data["username"],
                password=proxy_data["password"]
            )
        )

    def save_app_config(self) -> None:
        if self.app_config is None:
            return
        data = {
            "download_delay": self.app_config.download_delay,
            "max_workers": self.app_config.max_workers,
            "window_width": self.app_config.window_width,
            "window_height": self.app_config.window_height,
            "proxy": {
                "enabled": self.app_config.proxy.enabled,
                "type": self.app_config.proxy.proxy_type,
                "host": self.app_config.proxy.host,
                "port": self.app_config.proxy.port,
                "username": self.app_config.proxy.username,
                "password": self.app_config.proxy.password
            }
        }
        with open(self.app_config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_site_by_url(self, url: str) -> Optional[SiteConfig]:
        domain = urlparse(url).netloc
        for site in self.sites:
            if domain == site.domain or domain.endswith(f".{site.domain}"):
                return site
        return None