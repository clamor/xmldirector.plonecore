# -*- coding: utf-8 -*-

################################################################
# zopyx.existdb
# (C) 2014,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import requests
from requests.auth import HTTPBasicAuth

from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from zExceptions import Forbidden
from zExceptions import NotFound

from zopyx.existdb.interfaces import IExistDBSettings


class ExistDBError(Exception):
    pass


class API(BrowserView):

    def generic_query(self, script_path='all-documents', output_format='json', deserialize_json=False, **kw):
        """ Public query API for calling xquery scripts through RESTXQ.
            The related xquery script must expose is functionality through
            http://host:port/exist/restxq/<script_path>.<output_format>.
            The result is then returned text (html, xml) or deserialized JSON
            data structure.
            Note that <script_path> must start with '/db/' or 'db/'.
        """

        if not self.context.api_enabled:
            raise Forbidden('API not enabled')

        if output_format not in ('json', 'xml', 'html'):
            raise NotFound(
                'Unsupported output format "{}"'.format(output_format))

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExistDBSettings)
        url = '{}/exist/restxq/{}.{}'.format(
            settings.existdb_url, script_path, output_format)
        result = requests.get(url,
                              auth=HTTPBasicAuth(settings.existdb_username,
                                                 settings.existdb_password),
                              params=kw)
        if result.status_code != 200:
            raise ExistDBError(
                'eXist-db return an response with HTTP code {} for {}'.format(result.status_code, url))

        if output_format == 'json':
            data = result.json()
            if deserialize_json:
                # called internally (and not through the web)
                data = result.json()
                return data
            else:
                data = result.text
                self.request.response.setHeader(
                    'content-type', 'application/json')
                self.request.response.setHeader('content-length', len(data))
                return data
        else:
            data = result.text
            self.request.response.setHeader(
                'content-type', 'text/{}'.format(output_format))
            self.request.response.setHeader('content-length', len(data))
            return data
