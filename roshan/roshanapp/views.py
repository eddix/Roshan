from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth
from roshan.roshanapp.models import *

import re
import sys
import os
import socket
import time
from json import dumps as jdumps

from lib import zookeeper as zk
import zkconfig
import zkutils

zkutils.set_default_retry(zkconfig.retry)

zh = -1

def check_path_perm(request, path):
    allow_access = False
    for perm_path in request.user.path_set.all():
        # Allow path
        if perm_path.perm == True:
            if path.startswith(perm_path.path) or perm_path.path.startswith(path):
                allow_access = True
        # Deny path
        if perm_path.perm == False:
            if path.startswith(perm_path.path):
                allow_access = False
                break
    return allow_access


class node_func(object):

    def __init__(self, func):
        self.func = func
        
    def __call__(self, request, path='/'):
        if not request.user.is_authenticated():
            return HttpResponse(jdumps({"error": "You need to login first."}))

        # Check posting data encoding.
        for k,v in request.POST.items():
            try:
                v.encode('ascii')
            except UnicodeEncodeError, errmsg:
                return HttpResponse(jdumps({"error": 'Invalid encoding.<br />' \
                        'Only ASCII code can be used in roshan.'}))

        # Get node variable
        path = request.POST.get('node', os.path.join("/", path))

        # Initial zookeeper handler
        if check_path_perm(request, path):
            global zh
            zh = zkutils.inithandler(zkconfig.servers)
            try:
                ret = self.func(request, path)
            except Exception, errmsg:
                ret = HttpResponse(jdumps({"error": "Call function error: " + str(errmsg)}))
            zk.close(zh)
            return ret
        else:
            return HttpResponse(jdumps({"error": "You are denied to access this node."}))

def index(request):
    redirect_uri = request.META.get('REQUEST_URI', '/')
    if not redirect_uri.endswith('/'):
        redirect_uri += '/'
    redirect_uri += 'static/index.html'
    return HttpResponseRedirect(redirect_uri)

def islogin(request):
    if request.user.is_authenticated():
        return HttpResponse('true')
    else:
        return HttpResponse('false')

def getlogin(request):
    if request.user.is_authenticated():
        return HttpResponse(request.user.username)
    else:
        return HttpResponse('false')

def login(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponse('ok')
        else:
            return HttpResponse('username or password is incorrect')
    except KeyError:
        return HttpResponse('username or password is missing')

def logout(request):
    auth.logout(request)
    redirect_uri = request.META.get('REQUEST_URI', '/')
    if not redirect_uri.endswith('/'):
        redirect_uri += '/'
    redirect_uri = redirect_uri.replace('logout/', 'static/index.html')
    return HttpResponseRedirect(redirect_uri)


def serverlist(request):
    stats = []
    for zkserver in zkconfig.servers:
        server_dict = {"id": zkserver[0], "text": zkserver[0], "leaf": True}
        stat = zkutils.stat(zkserver)
        if stat == False:
            server_dict['cls'] = 'failed'
        elif "Mode: leader" in stat:
            server_dict['cls'] = 'leader'
        elif "Mode: follower" in stat:
            server_dict['cls'] = 'follower'
        stats.append(server_dict)
    return HttpResponse(jdumps(stats))


def serverstat(request, server):
    server_stat = {'server':server,'properties':[],'clients':[]}
    servers_dict = dict(zkconfig.servers)
    if server not in servers_dict:
        server_stat['error'] = 'No this server'
        return HttpResponse(jdumps(server_stat))
    stat = zkutils.stat((server,servers_dict[server]))
    if stat == False:
        server_stat['error'] == 'failed'
    else:
        version_regex = re.compile(r'(Zookeeper version.*)')
        client_regex = re.compile("\s+\/(?P<ip>[\d\.]+):(?P<port>\d+)\[\d+\]\(queued=(?P<queued>\d+),recved=(?P<recved>\d+),sent=(?P<sent>\d+)\)")
        for line in stat.split('\n'):
            if line.startswith('Clients') or line == "":
                continue
            if version_regex.match(line):
                server_stat['version'] = line
            elif client_regex.match(line):
                mo = client_regex.match(line)
                client_dict = mo.groupdict()
                client_dict['host'] = zkutils.ip2host(client_dict['ip'])
                server_stat['clients'].append(client_dict)
            else:
                n,v = line.split(':',1)
                server_stat['properties'].append({"name":n, "value":v})
    return HttpResponse(jdumps(server_stat))


@node_func
def get(request, path='/'):
    node_dict = {'path': path, 'acl':[], 'data':'', 'stat':[]}
    stat,acls = zkutils._get_acl(zh,path)
    if stat != False:
        acls = zkutils.AclSet(acls).to_display_dict()
        for acl in acls:
            hostname = "all"
            if acl['scheme'] == 'ip':
                try:
                    hostname = socket.gethostbyaddr(acl['id'])[0]
                except socket.herror,errmsg:
                    hostname = 'Unknow host'
            acl['host'] = hostname
            # javascript conflict with 'id' key.
            acl['acl_id'] = acl['id']
            acl.pop('id')
            node_dict['acl'].append(acl)

    stat,data = zkutils._get(zh,path)
    if stat != False:
        node_dict['data'] = data
    else:
        node_dict['data'] = "error: Get Node Data Failed"

    stats = zkutils._get_stat(zh,path)
    if stats == False:
        node_dict['stat'] = {"error":'Get Node Stat Failed'}
    else:
        stat_keys = stats.keys()
        # stat_keys.sort()
        for k in stat_keys:
            node_dict['stat'].append({"name":k,"value":stats[k]})
        node_dict['stat'].append({
            'name':'Created Time',
            'value':time.strftime("%F %X", time.localtime(float(stats['ctime']/1000.0)))
        })
        node_dict['stat'].append({
            'name':'Modified Time',
            'value':time.strftime("%F %X", time.localtime(float(stats['mtime']/1000.0)))
        })
        node_dict['stat'].append({
            'name': 'Acl Counts',
            'value': len(node_dict['acl'])
        })
    return HttpResponse(jdumps(node_dict))


@node_func
def add(request, path='/'):
    stat = zkutils._get_stat(zh, path)
    if stat:
        return HttpResponse(jdumps({'error': 'Node already exists'}))
    control_masters = list(zkconfig.control_machines)
    control_masters.append("127.0.0.1")
    control_masters.append(socket.gethostbyname(socket.gethostname()))
    default_acl = zkutils.AclSet(["ip:%s:31" %(id) for id in control_masters])
    try:
        ret = zk.create(zh, path, "", default_acl.to_dict())
        if ret == path:
            return HttpResponse(jdumps({'status':'ok'}))
        else:
            return HttpResponse(jdumps({'error':str(ret)}))
    except IOError, errmsg:
        return HttpResponse(jdumps({'error': str(errmsg)}))

@node_func
def update(request, path='/'):
    update_stat = ""
    # set data for this node
    if 'data' in request.POST:
        data = request.POST['data']
        stat, old_data = zkutils._get(zh, path)
        try:
            ret = zk.set(zh, path, data, stat['version'])
        except IOError, errmsg:
            update_stat += ("Set data error: %s"%str(errmsg))
    # set acl for this node
    if 'acl' in request.POST:
        # add control machine into list.
        control_masters = list(zkconfig.control_machines)
        control_masters.append("127.0.0.1")
        control_masters.append(socket.gethostbyname(socket.gethostname()))
        control_masters = list(set(control_masters))
        acl_set = zkutils.AclSet(["ip:%s:31" %(id) for id in control_masters])
        # user added acl
        acl_str = request.POST['acl']
        acl_set.addmany(acl_str.split())

        stat, oldacls = zkutils._get_acl(zh, path)
        if stat == False:
            update_stat += "Get old acls failed"
        else:
            if 'isappend' in request.POST and request.POST['isappend'] == 'on':
                acl_set.addmany(oldacls)
            try:
                ret = zk.set_acl(zh, path, stat['aversion'], acl_set.to_dict())
                if ret is not zk.OK:
                    raise IOError("set acl failed")
                # apply to ephemeral child
                children = zkutils._get_children(zh, path)
                if children[0] == False:
                    raise IOError('get children failed')
                for child in children[1]:
                    child_path = os.path.join(path, child)
                    stat, oldacls = zkutils._get_acl(zh, child_path)
                    if stat['ephemeralOwner'] == 0:
                        continue
                    ret = zk.set_acl(zh, child_path, stat['aversion'],
                        acl_set.to_dict())
                    if ret is not zk.OK:
                        raise IOError("set acl failed for %s"%(child_path))
            except IOError, errmsg:
                update_stat += str(errmsg)
            except ValueError, errmsg:
                update_stat += str(errmsg)
    if update_stat == '':
        update_ret = {'status': 'ok'}
    else:
        update_ret = {'error': update_stat}
    return HttpResponse(jdumps(update_ret))


@node_func
def delete(request, path='/'):
    try:
        ret = zk.delete(zh, path)
        print >> sys.stderr, path
        if ret == zk.OK:
            return HttpResponse(jdumps({'status':'ok'}))
    except IOError, errmsg:
        return HttpResponse(jdumps({'error':str(errmsg)}))


@node_func
def children(request, path='/'):
    childrens = []
    data = zkutils._get_children(zh, path)
    if data[0] == False:
        return HttpResponse(jdumps({"error":str(data[1])}))
    for child in data[1]:
        child_path = os.path.join(path, child)
        if child_path == '/zookeeper':
            continue
        if check_path_perm(request, child_path) == False:
            continue
        child_dict = {"text":child, "id": child_path}
        stat = zkutils._get_stat(zh, child_path)
        if stat != False and stat['numChildren'] > 0:
            child_dict['leaf'] = False
        else:
            child_dict['leaf'] = True
        childrens.append(child_dict)
    return HttpResponse(jdumps(childrens))
