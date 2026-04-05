import os
from dotenv import load_dotenv
load_dotenv()

from image_service import ImageService

def test_pollinations():
    print("Testing Pollinations.ai Engine...")
    os.environ["IMAGE_ENGINE"] = "pollinations"
    keyword = "artificial intelligence"
    count = 2
    
    images = ImageService.fetch_topic_images(keyword, count)
    print(f"Fetched {len(images)} images.")
    for i, img_path in enumerate(images):
        if os.path.exists(img_path):
            print(f"Image {i+1} exists at: {img_path}")
            # Clean up
            # os.remove(img_path)
        else:
            print(f"Image {i+1} NOT FOUND at: {img_path}")

def test_unsplash():
    print("\nTesting Unsplash Engine...")
    os.environ["IMAGE_ENGINE"] = "unsplash"
    keyword = "nature"
    count = 2
    
    images = ImageService.fetch_topic_images(keyword, count)
    print(f"Fetched {len(images)} images.")
    for i, img_path in enumerate(images):
        if os.path.exists(img_path):
            print(f"Image {i+1} exists at: {img_path}")
        else:
            print(f"Image {i+1} NOT FOUND at: {img_path}")

if __name__ == "__main__":
    test_pollinations()
    test_unsplash()
