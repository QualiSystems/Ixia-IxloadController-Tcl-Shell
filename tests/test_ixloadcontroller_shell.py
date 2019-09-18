#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import json
import unittest

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

controller = '192.168.15.23'
client_install_path = 'C:/Program Files (x86)/Ixia/IxLoad/8.40-EA'

attributes = [AttributeNameValue('Client Install Path', client_install_path),
              AttributeNameValue('Controller Address', controller)]

ports = ['IxLoad/Module1/Port1', 'IxLoad 2/Module1/Port1']


class TestIxLoadControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxLoad Controller Tcl', attributes)

    def tearDown(self):
        self.session.EndReservation(self.context.reservation.reservation_id)
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config_840.rxf'))

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'bhrtest.rxf'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller Tcl', 'Service',
                                    'start_test', [InputNameValue('blocking', 'True')])
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id,
                                            'IxLoad Controller Tcl', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Test_Client'),
                                                               InputNameValue('output_type', 'JSON')])
        assert(int(json.loads(stats.Output)['20']['TCP Connections Established']) >= 0)

        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller Tcl', 'Service',
                                    'start_test', [InputNameValue('blocking', 'False')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller Tcl', 'Service',
                                    'stop_test')
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id,
                                            'IxLoad Controller Tcl', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Test_Client'),
                                                               InputNameValue('output_type', 'JSON')])
        try:
            assert(int(json.loads(stats.Output)['20']['TCP Connections Established']) >= 0)
        except KeyError as _:
            return
        raise Exception('Too many entries in stats...')

    def _load_config(self, config):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller Tcl', 'Service',
                                    'load_config', [InputNameValue('ixl_config_file_name', config)])


if __name__ == '__main__':
    sys.exit(unittest.main())
