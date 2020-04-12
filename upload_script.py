import asyncio

from bugatti_client import BugattiClient
from config import *

async def main():
    try:
        client = BugattiClient(api_entrypoint)
        await client.upload_config(upload_config_info['device_id'], upload_config_info['filename'])
    except Exception as e:
        print(e)


asyncio.run(main())