"""
ImageAgent - 智能图片搜索和管理
支持多个图片源: Unsplash, Pexels
"""
import os
import requests
from typing import List, Dict, Optional
from urllib.parse import quote
import hashlib
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

class ImageSource:
    """图片源基类"""

    def search(self, query: str, per_page: int = 5) -> List[Dict]:
        """
        搜索图片

        Args:
            query: 搜索关键词
            per_page: 返回数量

        Returns:
            图片信息列表
        """
        raise NotImplementedError


class UnsplashSource(ImageSource):
    """Unsplash图片源"""

    def __init__(self, access_key: str = None):
        """
        初始化Unsplash源

        Args:
            access_key: Unsplash API密钥
        """
        # Unsplash提供免费的API,需要注册获取access_key
        # https://unsplash.com/developers
        self.access_key = access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.base_url = "https://api.unsplash.com"

    def search(self, query: str, per_page: int = 5) -> List[Dict]:
        """搜索图片"""
        if not self.access_key:
            print("⚠️  未配置Unsplash API密钥,使用模拟数据")
            return self._mock_results(query, per_page)

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"  # 横向图片更适合PPT
            }
            headers = {
                "Authorization": f"Client-ID {self.access_key}"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("results", []):
                results.append({
                    "id": item["id"],
                    "url": item["urls"]["regular"],  # 中等尺寸
                    "download_url": item["urls"]["full"],  # 高清
                    "thumbnail": item["urls"]["thumb"],
                    "width": item["width"],
                    "height": item["height"],
                    "description": item.get("description", ""),
                    "author": item["user"]["name"],
                    "author_url": item["user"]["links"]["html"],
                    "source": "unsplash"
                })

            return results

        except Exception as e:
            print(f"⚠️  Unsplash搜索失败: {str(e)}")
            return self._mock_results(query, per_page)

    def _mock_results(self, query: str, per_page: int) -> List[Dict]:
        """返回模拟结果"""
        return [
            {
                "id": f"mock_{i}",
                "url": f"https://picsum.photos/800/600?random={hash(query) + i}",
                "download_url": f"https://picsum.photos/1920/1080?random={hash(query) + i}",
                "thumbnail": f"https://picsum.photos/200/150?random={hash(query) + i}",
                "width": 800,
                "height": 600,
                "description": f"Mock image for {query}",
                "author": "Lorem Picsum",
                "author_url": "https://picsum.photos",
                "source": "mock"
            }
            for i in range(per_page)
        ]


class PexelsSource(ImageSource):
    """Pexels图片源"""

    def __init__(self, api_key: str = None):
        """
        初始化Pexels源

        Args:
            api_key: Pexels API密钥
        """
        # Pexels也提供免费API
        # https://www.pexels.com/api/
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.base_url = "https://api.pexels.com/v1"

    def search(self, query: str, per_page: int = 5) -> List[Dict]:
        """搜索图片"""
        if not self.api_key:
            print("⚠️  未配置Pexels API密钥,使用模拟数据")
            return self._mock_results(query, per_page)

        try:
            url = f"{self.base_url}/search"
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            }
            headers = {
                "Authorization": self.api_key
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("photos", []):
                results.append({
                    "id": str(item["id"]),
                    "url": item["src"]["large"],
                    "download_url": item["src"]["original"],
                    "thumbnail": item["src"]["small"],
                    "width": item["width"],
                    "height": item["height"],
                    "description": item.get("alt", ""),
                    "author": item["photographer"],
                    "author_url": item["photographer_url"],
                    "source": "pexels"
                })

            return results

        except Exception as e:
            print(f"⚠️  Pexels搜索失败: {str(e)}")
            return self._mock_results(query, per_page)

    def _mock_results(self, query: str, per_page: int) -> List[Dict]:
        """返回模拟结果"""
        return [
            {
                "id": f"pexels_mock_{i}",
                "url": f"https://picsum.photos/800/600?random={hash(query) * 2 + i}",
                "download_url": f"https://picsum.photos/1920/1080?random={hash(query) * 2 + i}",
                "thumbnail": f"https://picsum.photos/200/150?random={hash(query) * 2 + i}",
                "width": 800,
                "height": 600,
                "description": f"Pexels mock for {query}",
                "author": "Mock Photographer",
                "author_url": "https://pexels.com",
                "source": "pexels_mock"
            }
            for i in range(per_page)
        ]


class ImageAgent:
    """智能图片Agent"""

    def __init__(self, cache_dir: str = "output/image_cache"):
        """
        初始化ImageAgent

        Args:
            cache_dir: 图片缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化图片源
        self.sources = {
            "unsplash": UnsplashSource(),
            "pexels": PexelsSource()
        }

        self.default_source = "unsplash"

    def generate_search_keywords(
            self,
            slide_title: str,
            slide_content: List[str],
            overall_topic: str
    ) -> List[str]:
        """
        根据页面内容生成搜索关键词

        Args:
            slide_title: 页面标题
            slide_content: 页面内容
            overall_topic: 整体主题

        Returns:
            关键词列表
        """
        keywords = []

        # 主关键词:标题
        if slide_title:
            keywords.append(slide_title)

        # 备选关键词:主题
        if overall_topic:
            keywords.append(overall_topic)

        # 提取内容中的关键名词(简单版)
        # 实际项目中可以使用NLP工具提取关键词
        for content in slide_content[:2]:  # 只看前2个要点
            words = content.split()
            if len(words) > 0:
                keywords.append(words[0])

        return keywords[:3]  # 最多3个关键词

    def search_images(
            self,
            keywords: List[str],
            num_results: int = 3,
            source: str = None
    ) -> List[Dict]:
        """
        搜索图片

        Args:
            keywords: 关键词列表
            num_results: 每个关键词返回的结果数
            source: 图片源名称

        Returns:
            图片信息列表
        """
        source_name = source or self.default_source
        image_source = self.sources.get(source_name)

        if not image_source:
            print(f"⚠️  未知图片源: {source_name}")
            return []

        all_results = []

        for keyword in keywords:
            print(f"   🔍 搜索图片: {keyword}")
            results = image_source.search(keyword, per_page=num_results)
            all_results.extend(results)

            if len(all_results) >= num_results * 2:
                break  # 已经足够了

        # 去重
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)

        return unique_results[:num_results * 2]

    def download_image(self, image_info: Dict) -> Optional[str]:
        """
        下载图片到本地

        Args:
            image_info: 图片信息

        Returns:
            本地文件路径
        """
        try:
            # 生成缓存文件名
            image_id = image_info["id"]
            ext = "jpg"
            filename = f"{image_id}.{ext}"
            filepath = self.cache_dir / filename

            # 如果已缓存,直接返回
            if filepath.exists():
                return str(filepath)

            # 下载图片
            url = image_info.get("download_url") or image_info["url"]
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 保存到本地
            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"   ✅ 图片已下载: {filename}")
            return str(filepath)

        except Exception as e:
            print(f"   ⚠️  图片下载失败: {str(e)}")
            return None

    def select_best_image(
            self,
            images: List[Dict],
            slide_context: Dict
    ) -> Optional[Dict]:
        """
        从候选图片中选择最合适的

        Args:
            images: 候选图片列表
            slide_context: 页面上下文信息

        Returns:
            最佳图片信息
        """
        if not images:
            return None

        # 简单策略:选择第一个
        # 实际项目中可以使用AI评分选择
        return images[0]

    def get_image_for_slide(
            self,
            slide_title: str,
            slide_content: List[str],
            overall_topic: str
    ) -> Optional[str]:
        """
        为页面获取合适的图片

        Args:
            slide_title: 页面标题
            slide_content: 页面内容
            overall_topic: 整体主题

        Returns:
            本地图片路径
        """
        # 1. 生成关键词
        keywords = self.generate_search_keywords(
            slide_title,
            slide_content,
            overall_topic
        )

        if not keywords:
            print("   ⚠️  无法生成搜索关键词")
            return None

        # 2. 搜索图片
        images = self.search_images(keywords, num_results=2)

        if not images:
            print("   ⚠️  未找到合适的图片")
            return None

        # 3. 选择最佳图片
        best_image = self.select_best_image(
            images,
            {"title": slide_title}
        )

        if not best_image:
            return None

        # 4. 下载图片
        local_path = self.download_image(best_image)

        return local_path

    def clear_cache(self) -> None:
        """清空图片缓存"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True)
        print("✅ 图片缓存已清空")