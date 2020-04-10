import asyncio
import hashlib

from t_cloud_client import TCloudClient
from config import *

async def main():
    try:
        client = TCloudClient(api_entrypoint)
        # test = client._get_token('')
        await client.upload_config(upload_config_info['device_id'], upload_config_info['filename'])
    except Exception as e:
        print(e)


asyncio.run(main())