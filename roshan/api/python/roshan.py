import urllib
import httplib
import json

__doc__ == """
Roshan Python API - by eddix<elitecharm@gmail.com>

Usage:
### Sample: roshan_test.py

from roshan import Roshan

# Initial Roshan class, and login
roshan = Roshan(host='zookeeper.myhost.com', port=80, baseurl='/roshan')
roshan.login('sandbox', 'sandbox')

# List children of node
nodes = roshan.get_node_list('/sandbox')
if nodes is not None:
    for node in nodes:
        if not node.get('leaf', False) == True:
            print node['text']
        else:
            print '%s/'%(node['text'])

# Add, update and delete an node
roshan.add_node('/sandbox/roshan-api')
roshan.update_node('/sandbox/roshan-api', data='Only English Now')
roshan.delete_node('/sandbox/roshan-api')
"""

__DEBUG__ = False


class Roshan(object):
    """Roshan client class"""

    host = 'zookeeper.myhost.com'
    port = 10086
    baseurl = '/roshan/'
    user_agent = 'Roshan Python API'

    def __init__(self, host=None, port=None, baseurl=None):
        """params `host`, `port` and `baseurl` will overwrite default
        settings"""
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if baseurl is not None:
            self.baseurl = baseurl
        self._conn = httplib.HTTPConnection(self.host, self.port)
        self._header = {'User-Agent': self.user_agent}

    def __request(self, url, params=None, method='GET'):
        """wrapped function, send request to roshan server"""
        if params is not None:
            params = urllib.urlencode(params)
        url = self.baseurl + url
        self._conn.request(method, url, params, self._header)
        res = self._conn.getresponse()
        if __DEBUG__:
            print url
            print res.status
            print res.reason
            print res.read()
        if 200 == int(res.status):
            cookie = res.getheader('Set-Cookie', None)
            if cookie is not None:
                _cookie = cookie.split(';')[0]
                self._header.update({'Cookie': _cookie})
            return res.read()
        return None

    def __get_text(self, url, params=None):
        ret = self.__request(url, params)
        if ret is not None:
            return ret
        return False

    def __get_json(self, url, params=None):
        ret = self.__request(url, params)
        if ret is not None:
            return json.loads(ret)
        return False

    def __post_text(self, url=None, params=None):
        ret = self.__request(url, params, 'POST')
        if ret is not None:
            return ret
        return False

    def __post_json(self, url=None, params=None):
        ret = self.__request(url, params, 'POST')
        if ret is not None:
            return json.loads(ret)
        return False

    def login(self, username, password):
        params = dict(username=username, password=password)
        return self.__post_text('login/', params)

    def logout(self):
        self.__request('logout/')

    def get_server_stat(self, server):
        return self.__get_json('server/stat/' + server + '/')

    def get_server_list(self):
        return self.__get_json('server/list/')

    def get_node_list(self, node='/'):
        params = dict(node=node)
        return self.__post_json('node/list/', params)

    def get_node(self, node):
        params = dict(node=node)
        return self.__post_json('node/get/', params)

    def add_node(self, node):
        params = dict(node=node)
        return self.__post_json('node/add/', params)

    def update_node(self, node, acl=None, data=None, isappend=True):
        params = dict(node=node)
        if acl is not None:
            params.update(dict(acl=acl))
        if data is not None:
            params.update(dict(data=data))
        if isappend == True:
            params.update(dict(isappend='on'))
        return self.__post_json('node/update/', params)

    def delete_node(self, node):
        params = dict(node=node)
        return self.__post_json('node/delete/', params)

if __name__ == '__main__':
    print __doc__
