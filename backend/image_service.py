import os
import requests
import tempfile
import concurrent.futures
import random
from typing import List, Optional

class BaseEngine:
    def fetch_images(self, keyword: str, count: int = 15) -> List[str]:
        raise NotImplementedError

    def download_image(self, url: str) -> Optional[str]:
        """Download image and return path to temporary file."""
        try:
            if not url: return None
            response = requests.get(url, timeout=15)
            if response.status_code != 200: 
                print(f"Failed to download image from {url}: HTTP {response.status_code}")
                return None
            
            tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            with open(tmp_img.name, "wb") as f:
                f.write(response.content)
            return tmp_img.name
        except Exception as e:
            print(f"Download Error for {url}: {e}")
            return None

class UnsplashEngine(BaseEngine):
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")

    def fetch_images(self, keyword: str, count: int = 15) -> List[str]:
        """Fetch images from Unsplash API."""
        urls = []
        if not self.access_key:
            print("Warning: UNSPLASH_ACCESS_KEY not found in environment.")
            return []

        try:
            url = f"https://api.unsplash.com/search/photos?query={keyword}&orientation=landscape&per_page={count}&client_id={self.access_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                urls = [item["urls"]["regular"] for item in data.get("results", [])]
            else:
                print(f"Unsplash API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print("Unsplash API Exception:", e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(self.download_image, urls))
            return [r for r in results if r]

class PollinationsEngine(BaseEngine):
    def fetch_images(self, keyword: str, count: int = 15) -> List[str]:
        """Generate images using Pollinations.ai (Free Text-to-Image)."""
        # Generate varied prompts to get different images
        styles = [
            "realistic, high resolution, professional photography, cinematic lighting, 4k",
            "educational illustration, clean design, digital art, high quality",
            "concept art, detailed, vibrant colors, masterpiece",
            "symbolic representation, modern style, clean background",
            "infographic style, professional execution, sharp focus"
        ]
        
        urls = []
        for i in range(count):
            style = styles[i % len(styles)]
            prompt = f"{keyword}, {style}"
            seed = random.randint(1, 1000000)
            # Encode prompt for URL
            encoded_prompt = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
            urls.append(url)

        print(f"Generating {count} images via Pollinations.ai for: {keyword}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(self.download_image, urls))
            return [r for r in results if r]

class ImageService:
    _engines = {
        "unsplash": UnsplashEngine,
        "pollinations": PollinationsEngine
    }

    @classmethod
    def get_engine(cls):
        engine_name = os.getenv("IMAGE_ENGINE", "unsplash").lower()
        engine_class = cls._engines.get(engine_name, UnsplashEngine)
        return engine_class()

    @classmethod
    def fetch_topic_images(cls, keyword: str, count: int = 15) -> List[str]:
        """Main entry point to fetch images based on configured engine."""
        engine = cls.get_engine()
        images = engine.fetch_images(keyword, count)
        
        # Fallback to Unsplash if pollinations fails or returns nothing
        if not images and isinstance(engine, PollinationsEngine):
            print("Pollinations failed, falling back to Unsplash...")
            images = UnsplashEngine().fetch_images(keyword, count)
            
        return images
