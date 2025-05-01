import os
import requests
from urllib.parse import urlparse

def download_image(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")

def main():
    # Create static/images directory if it doesn't exist
    os.makedirs('static/images', exist_ok=True)
    
    # Sample image URLs for each menu item
    images = {
        'masala-chai.jpg': 'https://www.vegrecipesofindia.com/wp-content/uploads/2021/06/masala-chai-2.jpg',
        'lemon-tea.jpg': 'https://www.vegrecipesofindia.com/wp-content/uploads/2022/06/lemon-tea-1.jpg',
        'green-tea.jpg': 'https://www.vegrecipesofindia.com/wp-content/uploads/2022/05/green-tea-2.jpg',
        'misal-pav.jpg': 'https://www.vegrecipesofindia.com/wp-content/uploads/2010/07/misal-pav-recipe-1.jpg',
        'chicken-biryani.jpg': 'https://www.licious.in/blog/wp-content/uploads/2022/06/chicken-biryani-01.jpg',
        'mutton-biryani.jpg': 'https://www.licious.in/blog/wp-content/uploads/2022/12/Mutton-Biryani.jpg',
        'chicken-fried-rice.jpg': 'https://www.licious.in/blog/wp-content/uploads/2020/12/Chicken-Fried-Rice-min.jpg',
        'chicken-pizza.jpg': 'https://www.licious.in/blog/wp-content/uploads/2020/12/Chicken-Pizza.jpg'
    }
    
    for filename, url in images.items():
        filepath = os.path.join('static/images', filename)
        if not os.path.exists(filepath):
            download_image(url, filepath)
        else:
            print(f"Image {filename} already exists")

if __name__ == '__main__':
    main() 