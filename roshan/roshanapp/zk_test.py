#!/usr/bin/env python

# Unit test script for zkutils.py


import zkutils
import unittest

class ZkutilsTestCase(unittest.TestCase):

    def setUp(self):
        self.acl_set = zkutils.AclSet()

    def testAddList(self):
        self.acl_set.add(['ip', '127.0.0.1', '1'])
        assert "ip:127.0.0.1:1" in self.acl_set.to_string()
        self.acl_set.add(('ip', '127.0.0.2', 32)) # 31 is max number. 32 will be cast to 0.
        assert "ip:127.0.0.2:0" in self.acl_set.to_string()

    def testAddDict(self):
        self.acl_set.add({'scheme':'ip', 'id': '127.0.0.1', 'perms': '1'})
        assert "ip:127.0.0.1:1" in self.acl_set.to_string()
        self.acl_set.add({'scheme':'ip', 'id': '127.0.0.2', 'perms': 1})
        assert "ip:127.0.0.2:1" in self.acl_set.to_string()

    def testAddMany(self):
        many = ("ip:127.0.0.1:1",
            ['ip', '127.0.0.2', '1'],
            {'scheme': 'ip', 'id': '127.0.0.3', 'perms': 1})
        self.acl_set.addmany(many)
        assert "ip:127.0.0.1:1" in self.acl_set.to_string()
        assert "ip:127.0.0.2:1" in self.acl_set.to_string()
        assert "ip:127.0.0.3:1" in self.acl_set.to_string()

    def testWorldScheme(self):
        self.acl_set.add("world:anyone:31")
        assert "world:anyone:31" in self.acl_set.to_string()

if __name__ == '__main__':
    unittest.main()

