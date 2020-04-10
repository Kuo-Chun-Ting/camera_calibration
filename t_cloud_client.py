from tornado.httpclient import AsyncHTTPClient
from config import *
from pathlib import Path
import asyncio
import json
import uuid
import requests
import json
import hashlib
import pathlib


class TCloudClient:
    def __init__(self, entrypoint, user=None):
        self._token = None
        self._user = user
        self._entrypoint = entrypoint
        self._headers = {'accept':'application/json',
                        'Authorization': None,
                        'Content-Type': 'application/json'}
        self._http_client = AsyncHTTPClient()

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
            url = f'{self._entrypoint}auth/token'

            headers = {'X-TCLOUD-SERVICE': 'fm',
                        'Content-Type': 'application/json'}

            body = json.dumps(self._user)

            response = await self._http_client.fetch(url,
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
    
    async def _get_device_token(self, _device_id):
        """Get the access token from Alpha."""

        try:
            url = f'{self._entrypoint}auth/device/token'

            # data = 'e42c56dbfdb7dbc34ded-f25d-488d-bf68-e822b4f6dd2a0P-69-00-DB-FD-B71586507721'.encode('utf-8')
            # s = hashlib.sha1()
            # s.update(data)
            # h = s.hexdigest()
            # print(h)
            
            body = json.dumps({
                "auth_digest": "b249445fa3cdfccaf48ed270075b805d2d9c7ecc",
                "serial_number": "0P-69-00-DB-FD-B7",
                "timestamp": 1586507721,
                "uuid": "dbc34ded-f25d-488d-bf68-e822b4f6dd2a"
                })
            
            headers = {k: v for k, v in self._headers.items() if v is not None}

            response = await self._http_client.fetch(url,
                                            raise_error=True,
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

    async def _device_auth_promise_fetch(self, device_id, fetch):
        response = await fetch()
        if response.code in (401, 599):
                await self._get_device_token(device_id)
                return await fetch()
        return response
    
    async def _get_cams(self, device_id):
        """List cameras by device_id."""

        url = f'{self._entrypoint}streamer/{device_id}/cams?bypass_status_check=false'
       
        async def fetch():
            return await self._http_client.fetch(url,
                                            raise_error=False,
                                            method='GET',
                                            headers=self._headers)
        return await self._auth_promise_fetch(fetch)

    async def _get_cam_id(self, device_id, cam_name):
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

    async def _patch_setting(self,device_id, filename):
        """Upliad the config of the wheel calibration"""
        
        url = f'{self._entrypoint}event_resource/setting'
       
        
        with open(filename,'r') as f:
            data = json.load(f)
        body = json.dumps(data)
        method = 'PATCH'
        async def fetch():
            return await self._http_client.fetch(url,
                                        raise_error=False,
                                        method=method,
                                        body=body,
                                        headers=self._headers
                                        )
        return await self._device_auth_promise_fetch(device_id, fetch)
             
    async def download_video(self, device_id, cam_name, start, duration):
        """Download video
        
        :param start: Timestamp string.
        :param duration: int number, unit seconds
        """
        
        try:
            filename = f'{cam_name}-{start}-{duration}.mkv'
            if Path(filename).is_file():
                print(f'{filename} already exist.')
                return filename
            
            print('Getting camera id...')
            cam_id = await self._get_cam_id(device_id, cam_name)
            
            print('Video downloading...')
            url = f'{self._entrypoint}streamer/{device_id}/cams/{cam_id}/clip?pos={start}&duration={duration}&profile=-1'
            with requests.get(url, stream=True, headers=self._headers) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            # f.flush()
            
            print('done')
            return filename
        except Exception as e:
            print(e)
            return None
 
    async def upload_config(self, device_id, filename):
        """Upliad the config of the wheel calibration.
        
        :param start: Timestamp string.
        :param duration: int number, unit seconds
        """
        
        if not Path(filename).is_file():
            print(f"The config {filename} doesn't exist.")
            return False
        
        response = await self._patch_setting(device_id, filename)
        if not response.error:
            return True
        else:
            print(f'{response.error}')
            return False


