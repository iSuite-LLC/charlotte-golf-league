import cloudinary
import cloudinary.api
import json
import os
from pathlib import Path

PHOTOS_JSON = Path(__file__).parent.parent / 'Dashboard' / 'photos.json'

def main():
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key    = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')

    if not all([cloud_name, api_key, api_secret]):
        print('Cloudinary credentials not set — skipping photo sync')
        if not PHOTOS_JSON.exists():
            PHOTOS_JSON.write_text('{"photos":[]}', encoding='utf-8')
        return

    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True)

    resources, next_cursor = [], None
    while True:
        kwargs = dict(type='upload', prefix='golf-league/', max_results=100, resource_type='image')
        if next_cursor:
            kwargs['next_cursor'] = next_cursor
        result      = cloudinary.api.resources(**kwargs)
        resources  += result.get('resources', [])
        next_cursor = result.get('next_cursor')
        if not next_cursor:
            break

    photos = [
        {
            'url':        r['secure_url'],
            'public_id':  r['public_id'],
            'created_at': r['created_at'],
            'width':      r.get('width'),
            'height':     r.get('height'),
        }
        for r in resources
    ]
    photos.sort(key=lambda x: x['created_at'], reverse=True)

    with open(PHOTOS_JSON, 'w', encoding='utf-8') as f:
        json.dump({'photos': photos}, f, indent=2)

    print(f'photos.json written — {len(photos)} photo(s)')

if __name__ == '__main__':
    main()
