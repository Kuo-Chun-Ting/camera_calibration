import asyncio

from bugatti_client import BugattiClient
from config import *

async def main():
    try:
        client = BugattiClient(api_entrypoint, user=auth_user)
        response = await client.download_video(download_video_info['device_id'], 
                                                download_video_info['cam_name'], 
                                                download_video_info['start'], 
                                                download_video_info['duration'])
    except Exception as e:
        print(e)
    
asyncio.run(main())