from tornado.httpclient import AsyncHTTPClient
from config import *
from pathlib import Path
import asyncio
import json
import uuid
import requests


class StreamerClient:
    def __init__(self):
        self._token=None
        self._entry_point = streamer_entry_point
        self._headers = {'accept':'application/json',
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
                self._token = f"Bearer {json.loads(response.body)['msg']['v3']['access_token']}"
                self._headers['Authorization'] = self._token
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
    
    async def _get_cams(self, device_id):
        """List cameras by device_id."""

        api_endpoint = f'{self._entry_point}{device_id}/cams?bypass_status_check=false'
       
        async def fetch():
            return await self.http_client.fetch(api_endpoint,
                                            raise_error=False,
                                            method='GET',
                                            headers=self._headers)
        return await self._auth_promise_fetch(fetch)

    async def get_cam_id(self, device_id, cam_name):
        """Get the camera by the given device and camera name"""
        
        
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
           
    def download_video(self, cam_id, device_id, start, duration, filename):
        """Download video to current folder.
        
        :param start: timestamp string eg.'1586495803'.
        :param duration: unit is second and type is int.
        :param filename: the name gonna be saved.
        """
        
        
        try:
            print('Video downloading...')
            
            url = f'{self._entry_point}{device_id}/cams/{cam_id}/clip?pos={start}&duration={duration}&profile=-1'
            with requests.get(url, stream=True, headers=self._headers) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            # f.flush()
            
            print('done')
        except Exception as e:
            print(e)




