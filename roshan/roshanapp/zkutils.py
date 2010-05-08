# zookeeper utilities lib
#
# Provide simple and quick operate functions
# to view and modify zookeeper.
#
# Author: eddix<elitecharm@gmail.com>
# Date: 2009/11/11
#
# Last modify: 2009/12/09

import socket
from lib import zookeeper as zk

_retry = 2
_data_buffer_len_ = 16 * 1024


class AclFormatError(Exception):
    """Exception if acl format is error"""
    def __init__(self, msg):
        self.msg = msg


class AclSet():
    def __init__(self, acls=None):
        """acls is a list or tuple contain acls"""
        self.acls = set()
        if acls is not None:
            self.addmany(acls)

    def _aclnum2str(self, n):
        ret = ""
        if n & zk.PERM_READ: ret += 'r'
        if n & zk.PERM_WRITE: ret += 'w'
        if n & zk.PERM_CREATE: ret += 'c'
        if n & zk.PERM_DELETE: ret += 'd'
        if n & zk.PERM_ADMIN: ret += 'a'
        return ret
    
    def _aclstr2num(self, s):
        ret = 0
        s = s.lower()
        if 'r' in s: ret |= zk.PERM_READ
        if 'w' in s: ret |= zk.PERM_WRITE
        if 'c' in s: ret |= zk.PERM_CREATE
        if 'd' in s: ret |= zk.PERM_DELETE
        if 'a' in s: ret |= zk.PERM_ADMIN
        return ret
    
    def add(self, acl):
        if isinstance(acl, (str, unicode)):
            try:
                scheme, id, perms = acl.split(":")
                # convert it will ignore invalid number. such as perms 32 will be change to 0.
                if perms.isdigit():
                    perms = self._aclnum2str(int(perms))
                perms = self._aclstr2num(perms)
                self.acls.add(':'.join(map(str, [scheme, id, perms])))
            except ValueError:
                raise AclFormatError("Error format: " + acl)
        elif isinstance(acl, (list, tuple)):
            if len(acl) != 3:
                raise AclFormatError("Error format of acl. Need tuple or list with 3 items.")
            self.add(':'.join(map(str, acl)))
        elif isinstance(acl, dict):
            try:
                self.add(':'.join(map(str, [acl['scheme'], acl['id'], acl['perms']])))
            except KeyError:
                raise AclFormatError("Error format of acl. Need keys: scheme, id, perms")

    def addmany(self, acls):
        for acl in acls:
            self.add(acl)

    def remove(self, acl):
        import types
        if type(acl) == types.StringType:
            self.acls.remove(acl)
        elif type(acl) == types.TupleType or type(acl) == types.ListType:
            self.acls.remove(':'.join(acl))
        elif type(acl) == types.DictType:
            self.acls.remove(':'.join(map(str,
                            acl['scheme'], acl['id'], acls['perms'])))

    def to_string(self):
        return self.acls

    def to_display_dict(self):
        acls = self.to_dict()
        return acls

    def to_dict(self):
        acls = list()
        for acl in self.acls:
            scheme, id, perms = acl.split(':')
            perms = int(perms)
            acls.append({'scheme': scheme,
                         'id': id,
                         'perms': perms})
        return acls
        
def set_default_retry(n):
    global _retry
    _retry = n

def _get(zh, path):
    for r in range(0, _retry):
        try:
            data,stat = zk.get(zh, path, _data_buffer_len_)
            ret = (stat,data)
            break
        except IOError,errmsg:
            ret = (False, errmsg)
    return ret

def _get_acl(zh, path):
    for r in range(0, _retry):
        try:
            stat,acl = zk.get_acl(zh, path)
            ret = (stat,acl)
            break
        except IOError,errmsg:
            ret = (False, errmsg)
    return ret

def _get_children(zh, path):
    for r in range(0, _retry):
        try:
            children = zk.get_children(zh, path)
            ret = (True, children)
            break
        except IOError,errmsg:
            ret = (False, errmsg)
    return ret

def _get_stat(zh, path):
    for r in range(0, _retry):
        try:
            stat = zk.exists(zh, path)
            if stat:
                return stat
        finally:
            stat = False
    return False

def inithandler(servers):
    zk.set_debug_level(zk.LOG_LEVEL_WARN)
    serverlist = ','.join(["%s:%s"%(s[0],s[1]) for s in servers])
    return zk.init(serverlist)

def stat((server,port)):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    response = ""
    for r in range(0, _retry):
        try:
            sock.connect((server,port))
            sock.send("stat")
            while True:
                data = sock.recv(1024)
                if data == "":
                    break
                response += data
            break
        except socket.error,errmsg:
            response = False
    return response

def ip2host(ip):
    try:
        host = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        host = "Unknow Host"
    return host
