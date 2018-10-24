# Copyright (c) 2018 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import tempfile

from networking_ansible.tests.unit import base


class MockedConfigParser(mock.Mock):
    def __init__(self, conffile, sections):
        super(MockedConfigParser, self).__init__()
        self.sections = sections

    def parse(self):
        self.sections.update({'ansible:testhost': {}})

    @staticmethod
    def _parse_file(values, namespace):
        pass


class TestBuildAnsibleInventory(base.BaseTestCase):
    parse_config = False

    def test_build_ansible_inventory_empty_hosts(self):
        self.test_config_files = []
        self.setup_config()

        self.assertEqual(self.empty_inventory,
                         self.ansconfig.build_ansible_inventory())

    @mock.patch('networking_ansible.config.LOG')
    @mock.patch('networking_ansible.config.cfg.ConfigParser')
    def test_build_ansible_inventory_parser_error(self, mock_parser, mock_log):
        self.test_config_files = ['/etc/foo.conf']
        self.setup_config()

        mock_parser().parse.side_effect = IOError()
        self.assertEqual(self.empty_inventory,
                         self.ansconfig.build_ansible_inventory())
        mock_log.error.assert_called()

    @mock.patch('networking_ansible.config.cfg.ConfigParser',
                MockedConfigParser)
    def test_build_ansible_inventory_w_hosts(self):
        self.test_config_files = ['foo']
        self.setup_config()

        self.assertEqual(self.inventory,
                         self.ansconfig.build_ansible_inventory())

    def test_build_ansible_inventory_from_file(self):
        _, conffile = tempfile.mkstemp()
        fp = open(conffile, 'w')
        fp.write("[ansible:h1]\nmanage_vlans=0\n")
        fp.write("[ansible:h2]\nmanage_vlans=1\n")
        fp.write("[ansible:h3]\nmanage_vlans=false\n")
        fp.close()

        self.test_config_files = [conffile]
        self.setup_config()

        ansible_inventory = self.ansconfig.build_ansible_inventory()

        hosts = ansible_inventory['all']['hosts']
        self.assertEqual({'manage_vlans': False}, hosts['h1'])
        self.assertEqual({'manage_vlans': True}, hosts['h2'])
        self.assertEqual({'manage_vlans': False}, hosts['h3'])
