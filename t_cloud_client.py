from tornado.httpclient import AsyncHTTPClient
from config import *
import asyncio
import json
import uuid


class StreamerClient:
    def __init__(self):
        self.entry_point = streamer_entry_point
        self.headers = {'accept':'application/json',
                        'Authorization': None,
                        'Content-Type': 'application/json'}
        self.http_client = AsyncHTTPClient()

    def _get_msg(self, response):
        url = response.request.url
        method = response.request.method
        code = response.code
        if not response.error:
            print(f'{method} {url} {code}')
            return json.loads(response.body)['msg']
        print(f'{method} {url} {code}')
    
    async def _get_token(self):
        """Get the access token from Alpha."""

        try:
            api_endpoint = auth_entry_point

            headers = {'X-TCLOUD-SERVICE': 'fm',
                        'Content-Type': 'application/json'}

            body = json.dumps(auth_user)

            response = await self.http_client.fetch(api_endpoint,
                                            raise_error=False,
                                            method='POST',
                                            body=body,
                                            headers=headers)
            if response.error is None:
                token = f"Bearer {json.loads(response.body)['msg']['v3']['access_token']}"
                self.headers['Authorization'] = token
                print(f'Getting token successful.')
            else:
                print(f'Getting token failed.')

        except Exception as e:
            print(f'An error occurred while getting token {e}')

    async def _auth_promise_fetch(self, fetch):
        response = await fetch()
        if response.code in (401, 599):
                await self._get_token()
                return await fetch()
        return response
    
    async def _get_cams(self, device_id)-> list:
        """List cameras by device_id."""

        api_endpoint = f'{self.entry_point}{device_id}/cams?bypass_status_check=false'
       
        async def fetch():
            return await self.http_client.fetch(api_endpoint,
                                            raise_error=False,
                                            method='GET',
                                            headers=self.headers)
        return await self._auth_promise_fetch(fetch)

    async def get_driver_cam_id(self, device_id, cam_name):
        response = await self._get_cams(device_id)
        cams = self._get_msg(response)
        if not cams:
            print('Can not find any camera by the given device id.')
            return
        
        match_cams = [c for c in cams if c['name'] == cam_name]
        if not match_cams:
            print('Can not find any camera by the given camera name')
            return
        return match_cams[0]['cam_uid']
        
    async def down_video(self, device_id, cam_id, start, duration)->str:
        response = await self.client.post_route(self.test_name)
        id = self.get_msg(response)['id']
        return id
    
    
async def main():
    client = StreamerClient()
    cam_id = await client.get_driver_cam_id(device_id, driver_cam_name)
    print(cam_id)
    
asyncio.run(main())