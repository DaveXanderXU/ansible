# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_policy_rule import Parameters
    from library.bigip_policy_rule import ModuleParameters
    from library.bigip_policy_rule import ApiParameters
    from library.bigip_policy_rule import ModuleManager
    from library.bigip_policy_rule import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_policy_rule import Parameters
        from ansible.modules.network.f5.bigip_policy_rule import ModuleParameters
        from ansible.modules.network.f5.bigip_policy_rule import ApiParameters
        from ansible.modules.network.f5.bigip_policy_rule import ModuleManager
        from ansible.modules.network.f5.bigip_policy_rule import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters_policy(self):
        args = dict(
            policy='Policy - Foo'
        )
        p = ModuleParameters(params=args)
        assert p.policy == 'Policy - Foo'

    def test_module_parameters_actions(self):
        args = dict(
            actions=[
                dict(
                    type='forward',
                    pool='pool-svrs'
                )
            ]
        )
        p = ModuleParameters(params=args)
        assert len(p.actions) == 1

    def test_module_parameters_conditions(self):
        args = dict(
            conditions=[
                dict(
                    type='http_uri',
                    path_begins_with_any=['/ABC']
                )
            ]
        )
        p = ModuleParameters(params=args)
        assert len(p.conditions) == 1

    def test_module_parameters_name(self):
        args = dict(
            name='rule1'
        )
        p = ModuleParameters(params=args)
        assert p.name == 'rule1'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_policy_draft_rule_http-uri_forward.json')
        p = ApiParameters(params=args)
        assert len(p.actions) == 1
        assert len(p.conditions) == 1


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_policy_rule_no_existence(self, *args):
        set_module_args(dict(
            name="rule1",
            state='present',
            policy='policy1',
            actions=[
                dict(
                    type='forward',
                    pool='baz'
                )
            ],
            conditions=[
                dict(
                    type='http_uri',
                    path_begins_with_any=['/ABC']
                )
            ],
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=False)
        mm.publish_on_device = Mock(return_value=True)
        mm.draft_exists = Mock(return_value=False)
        mm._create_existing_policy_draft_on_device = Mock(return_value=True)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_policy_rule_idempotent_check(self, *args):
        set_module_args(dict(
            name="rule1",
            state='present',
            policy='policy1',
            actions=[
                dict(
                    type='forward',
                    pool='baz'
                )
            ],
            conditions=[
                dict(
                    type='http_uri',
                    path_begins_with_any=['/ABC']
                )
            ],
            password='password',
            server='localhost',
            user='admin'
        ))

        current = ApiParameters(load_fixture('load_ltm_policy_draft_rule_http-uri_forward.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.draft_exists = Mock(return_value=False)
        mm.update_on_device = Mock(return_value=True)
        mm._create_existing_policy_draft_on_device = Mock(return_value=True)
        mm.publish_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
