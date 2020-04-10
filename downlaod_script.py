import asyncio

from t_cloud_client import StreamerClient
from config import *

async def main():
    try:
        client = StreamerClient()
        cam_id = await client.get_cam_id(download_video_info['device_id'], 
                                        download_video_info['driver_cam_name'])
        response = client.download_video(cam_id,
                                        download_video_info['device_id'], 
                                        download_video_info['start'], 
                                        download_video_info['duration'],
                                        download_video_info['filename'])
    except Exception as e:
        print(e)
    
asyncio.run(main())