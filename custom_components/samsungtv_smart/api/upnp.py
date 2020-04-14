#Smartthings TV integration#
#import requests
import xml.etree.ElementTree as ET
import asyncio
from aiohttp import ClientConnectionError, ClientSession
from async_timeout import timeout
from typing import Any, Dict, List, Optional

DEFAULT_TIMEOUT = 0.2

class upnp:

    def __init__(self, host, session: Optional[ClientSession] = None):
        self.host = host
        self.mute = False
        self.volume = 0
        if session:
            self._session = session
            self._managed_session = False
        else:
            self._session = ClientSession()
            self._managed_session = True

    def __enter__(self):
        return self

    async def _SOAPrequest(self, action, arguments, protocole):
        headers = {'SOAPAction': '"urn:schemas-upnp-org:service:{protocole}:1#{action}"'.format(action=action, protocole=protocole), 'content-type': 'text/xml'}
        body = """<?xml version="1.0" encoding="utf-8"?>
                <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
                    <s:Body>
                    <u:{action} xmlns:u="urn:schemas-upnp-org:service:{protocole}:1">
                        <InstanceID>0</InstanceID>
                        {arguments}
                    </u:{action}>
                    </s:Body>
                </s:Envelope>""".format(action=action, arguments=arguments, protocole=protocole)
        response = None
        try:
            with timeout(DEFAULT_TIMEOUT):
                async with self._session.post(
                    f"http://{self.host}:9197/upnp/control/{protocole}1",
                    headers=headers,
                    data=body,
                    raise_for_status=True,
                ) as resp:
                    response = await resp.content.read()
        except:
            pass
        return response

    async def async_get_volume(self):
        response = await self._SOAPrequest('GetVolume', "<Channel>Master</Channel>", 'RenderingControl')
        if response is not None:
            volume_xml = response.decode('utf8')
            tree = ET.fromstring(volume_xml)
            for elem in tree.iter(tag='CurrentVolume'):
                self.volume = elem.text
        return self.volume

    async def async_set_volume(self, volume):
        await self._SOAPrequest('SetVolume', "<Channel>Master</Channel><DesiredVolume>{}</DesiredVolume>".format(volume), 'RenderingControl')

    async def async_get_mute(self):
        response = await self._SOAPrequest('GetMute', "<Channel>Master</Channel>", 'RenderingControl')
        if response is not None:
            # mute_xml = response.decode('utf8')
            tree = ET.fromstring(response.decode('utf8'))
            mute = 0
            for elem in tree.iter(tag='CurrentMute'):
                mute = elem.text
            if (int(mute) == 0):
                self.mute = False
            else:
                self.mute = True
        return self.mute

    async def async_set_current_media(self, url):
        """ Set media to playback and play it."""
        try:
            await self._SOAPrequest('SetAVTransportURI', "<CurrentURI>{url}</CurrentURI><CurrentURIMetaData></CurrentURIMetaData>".format(url=url), 'AVTransport')
            await self._SOAPrequest('Play', "<Speed>1</Speed>", 'AVTransport')
        except Exception:
            pass

    async def async_play(self):
        """ Play media that was already set as current."""
        try:
            await self._SOAPrequest('Play', "<Speed>1</Speed>", 'AVTransport')
        except Exception:
            pass
