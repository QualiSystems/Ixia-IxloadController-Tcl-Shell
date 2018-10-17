#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import logging

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

from driver import IxLoadControllerDriver

controller = '192.168.15.23'
port = '8080'
version = '8.01.106.3'
version = '8.40.0.277'

attributes = {'Controller Version': version,
              'Controller Address': controller,
              'Controller TCP Port': port}

ports = ['PS-2G/Module1/Port1', 'PS-2G/Module1/Port2']
ports = ['ixia 2g/Module1/Port1', 'ixia 2g/Module2/Port1']
ports = ['IxVM 801/Module1/Port1', 'IxVM 801/Module2/Port1']
ports = ['184/Module1/Port1', '185/Module1/Port1']


class TestIxLoadControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxLoad Controller', attributes)
        self.driver = IxLoadControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def tearDown(self):
        self.driver.cleanup()
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')
        self.driver.load_config(self.context, 'E:/workspace/python/PyIxLoad/ixload/test/configs/test_config_840.rxf')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'Test_Client', 'json')
        print self.driver.get_statistics(self.context, 'Test_Client', 'csv')

    def test_run_stop_run(self):
        self.test_load_config()
        self.driver.start_test(self.context, 'False')
        self.driver.stop_test(self.context)
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'Test_Client', 'json')
        print self.driver.get_statistics(self.context, 'Test_Client', 'csv')

    def negative_tests(self):
        test_config = os.path.dirname(__file__).replace('\\', '/') + '/test_config.rxf'
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port'
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic1@Network1')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        # cleanup
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')


if __name__ == '__main__':
    sys.exit(unittest.main())
