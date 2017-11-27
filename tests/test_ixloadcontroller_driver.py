#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import logging

from cloudshell.traffic.tg_helper import get_reservation_ports
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from driver import IxLoadControllerDriver

host = '192.168.30.35'
host = 'localhost'
controller = '192.168.30.35'
controller = 'localhost'
client_install_path = '/opt/ixia/ixload/8.01.106.3'
client_install_path = 'C:/Program Files (x86)/Ixia/IxLoad/8.30-EA'


class TestIxLoadControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(host, self.session,
                                              'ps test', 'IxLoad Controller', client_install_path)
        self.context.resource.attributes['Controller Address'] = controller
        self.driver = IxLoadControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')
        self.driver.load_config(self.context, 'E:/workspace/python/PyIxLoad/ixload/test/configs/test_config.rxf')

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
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        assert(len(reservation_ports) == 2)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic1@Network1')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context, test_config)
        # cleanup
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')


if __name__ == '__main__':
    sys.exit(unittest.main())
