from tornado.httpclient import AsyncHTTPClient
from config import *
from pathlib import Path
import asyncio
import json
import uuid
import requests
import json
import hashlib
import time


class TCloudClient:
    def __init__(self, entrypoint, user=None):
        self._user_token = ''
        self._device_token = ''
        self._user = user
        self._entrypoint = entrypoint
        self._http_client = AsyncHTTPClient()
       
    async def _get_user_token(self):
        """Get the access token from Alpha."""

        try:
            url = f'{self._entrypoint}auth/token'
            headers = {'X-TCLOUD-SERVICE': 'fm',
                        'Content-Type': 'application/json'}
            body = json.dumps(self._user)

            print(f'Getting user token...\nrequest: {url}\nheaders: {headers}\nbody: {body}')
            response = await self._http_client.fetch(request=url,
                                                    raise_error=False,
                                                    method='POST',
                                                    body=body,
                                                    headers=headers)
            if not response.error:
                self._user_token = f"Bearer {json.loads(response.body)['msg']['v3']['access_token']}"
                print(f'Getting user token successful.')
            else:
                print(f'Getting user token failed.\n{response.error}')

        except Exception as e:
            print(f'An exceptional error occurred while getting user toke. {e}')

    async def _get_device_token(self, device_id):
        """Get the access token from Alpha."""

        try:
            url = f'{self._entrypoint}auth/device/token'
            headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}
            
            uid = str(uuid.uuid4())
            last_six = device_id[-6:]
            serial = '0P-69-00-{}-{}-{}'.format(last_six[-6:-4],last_six[-4:-2],last_six[-2:]).upper()
            ts = int(time.time())
            digest = self._get_digest(device_id, uid, serial, ts)
            body = json.dumps({
                "auth_digest": digest,
                "serial_number": serial,
                "timestamp": ts,
                "uuid": uid
                })
            
            print(f'Getting device token...\nrequest: {url}\nheaders: {headers}\nbody: {body}')
            response = await self._http_client.fetch(request=url,
                                                    raise_error=False,
                                                    method='POST',
                                                    body=body,
                                                    headers=headers)
            if not response.error:
                self._device_token = f"Bearer {json.loads(response.body)['msg']['v3']['access_token']}"
                print(f'Getting device token successful.')
            else:
                print(f'Getting device token failed.\n{response.error}')

        except Exception as e:
            print(f'An exceptional error occurred while getting device token. {e}')

    def _get_digest(self, device_id, uid, serial, ts):
        data = f'{device_id}{uid}{serial}{ts}'.encode('utf-8')
        i = hashlib.sha1()
        i.update(data)
        h = i.hexdigest()
        return h
               
    async def _get_cams(self, device_id):
        """List cameras by device_id."""
        try:
            url = f'{self._entrypoint}streamer/{device_id}/cams?bypass_status_check=false'
            headers = {'Authorization':self._user_token,
                        'accept':'application/json',
                        'Content-Type':'application/json'}
            
            print(f'Getting camera list...\nrequest: {url}\nheaders: {headers}')
            response = await self._http_client.fetch(request=url,
                                                    raise_error=False,
                                                    method='GET',
                                                    headers=headers)
            if not response.error:
                print(f'Getting camera list Successful.')
                return json.loads(response.body)['msg']
            else:
                print(f'Getting camera list failed.\n{response.error}')
        except Exception as e:
            print(f'An error occurred while getting camera list. {e}')

    async def _get_cam_id(self, device_id, cam_name):
        """Get the camera by the given device and camera name"""
        
        cams = await self._get_cams(device_id)
        if not cams:
            return

        match_cams = [c for c in cams if c['name'] == cam_name]
        if not match_cams:
            print('Can not find any camera by the given camera name')
            return
        elif len(match_cams) > 1:
            print(f'More then one specified camera name {cam_name}.')
            return
        else:
            cam_id = match_cams[0]['cam_uid']
            print(f'Camera id is {cam_id}')
            return cam_id

    def _get_cam_clip(self, cam_id, device_id, start, duration, filename):
        try:
            url = f'{self._entrypoint}streamer/{device_id}/cams/{cam_id}/clip?pos={start}&duration={duration}&profile=-1'
            headers = {'Authorization':self._user_token,
                        'accept':'application/json',
                        'Content-Type':'application/json'}

            print('Video downloading...\nrequest: {url}\nheaders: {headers}')
            with requests.get(url, stream=True, headers=headers) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: 
                            f.write(chunk)
            print('Video downloading successful.')
            return True
        except Exception as e:
            print('Video downloading failed.')

    async def _patch_setting(self,device_id, filename):
        """Upliad the config of the wheel calibration"""
        
        try:
            url = f'{self._entrypoint}event_resource/setting'
            headers = {'Authorization':self._device_token,
                        'accept':'application/json',
                        'Content-Type':'application/json'}
            with open(filename,'r') as f:
                data = json.load(f)
            body = json.dumps(data)
            
            print(f'Uploading config...\nrequest: {url}\nheaders: {headers}\nbody{body}')
            response = await self._http_client.fetch(request=url,
                                                    raise_error=False,
                                                    method='PATCH',
                                                    body=body,
                                                    headers=headers)
            if not response.error:
                print('Uploading config successful.')
                return True
            else:
                print(f'Uploading config failed {response.error}')
                return False
        except Exception as e:
            print(f'An exceptional error occurred while uploading config. {e}')

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
            
            await self._get_user_token()
            if self._user_token:
                cam_id = await self._get_cam_id(device_id, cam_name)
                if cam_id:
                    if self._get_cam_clip(cam_id, device_id, start, duration, filename):
                        return filename
        except Exception as e:
            print(e)
 
    async def upload_config(self, device_id, filename):
        """Upliad the config of the wheel calibration."""
        
        try:
            if not Path(filename).is_file():
                print(f"The config {filename} doesn't exist.")
                return False
            
            await self._get_device_token(device_id)
            if self._device_token:
                return await self._patch_setting(device_id, filename)
        except Exception as e:
            print(f'{e}')
