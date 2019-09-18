#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

from driver import IxLoadControllerTclDriver

controller = '192.168.15.23'
client_install_path = 'C:/Program Files (x86)/Ixia/IxLoad/8.40-EA'

attributes = {'Client Install Path': client_install_path,
              'Controller Address': controller}

ports = ['IxLoad/Module1/Port1', 'IxLoad 2/Module1/Port1']


class TestIxLoadControllerDriver(object):

    def setup(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxLoad Controller Tcl', attributes)
        self.driver = IxLoadControllerTclDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def teardown(self):
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
        self.driver.load_config(self.context, 'E:/workspace/python/PyIxLoad/ixload/test/configs/bhrtest.rxf')

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

    def test_negative(self):
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
