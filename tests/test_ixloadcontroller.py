#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import unittest

from cloudshell.api.cloudshell_api import CloudShellAPISession

from driver import IxLoadControllerDriver
import tg_helper

controller = 'localhost'
client_install_path = 'C:/Program Files (x86)/Ixia/IxLoad/8.01-GA'


class TestIxLoadControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = CloudShellAPISession('localhost', 'admin', 'admin', 'Global')
        self.context = tg_helper.create_context(self.session, 'ixload test', 'IxLoad Controller', client_install_path)
        self.driver = IxLoadControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')
        self.driver.load_config(self.context, os.path.dirname(__file__).replace('\\', '/') + '/test_config.rxf')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'Test_Client', 'json')
        print self.driver.get_statistics(self.context, 'Test_Client', 'csv')

    def negative_tests(self):
        test_config = os.path.dirname(__file__).replace('\\', '/') + '/test_config.rxf'
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id)
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
