#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import unittest

from cloudshell.shell.core.context import (ResourceCommandContext, ResourceContextDetails, ReservationContextDetails,
                                           ConnectivityContext, AutoLoadCommandContext)
from cloudshell.api.cloudshell_api import CloudShellAPISession
from driver import IxLoadControllerDriver
from ixia_handler import get_reservation_ports

controller = 'localhost'
install_path = 'C:/Program Files (x86)/Ixia/IxLoad/8.20-EA'


def create_context(session):
    context = ResourceCommandContext()

    context.connectivity = ConnectivityContext()
    context.connectivity.server_address = 'localhost'
    context.connectivity.admin_auth_token = session.token_id

    response = session.CreateImmediateTopologyReservation('ixload unittest', 'admin', 60, False, False, 0,
                                                          'ixload test', [], [], [])

    context.resource = ResourceContextDetails()
    context.resource.name = 'IxLoad Controller'
    context.resource.address = controller
    context.resource.attributes = {'Client Install Path': install_path}

    context.reservation = ReservationContextDetails()
    context.reservation.reservation_id = response.Reservation.Id
    context.reservation.owner_user = response.Reservation.Owner
    context.reservation.domain = response.Reservation.DomainName

    return context


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = CloudShellAPISession('localhost', 'admin', 'admin', 'Global')
        self.context = create_context(self.session)
        self.driver = IxLoadControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_get_inventory(self):
        print self.driver.get_inventory(AutoLoadCommandContext())

    def test_load_config(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')
        self.driver.load_config(self.context, os.path.dirname(__file__).replace('\\', '/') + '/test_config.rxf')

    def run_traffic(self):
        self.test_load_config()
        self.driver.start_test(self.context, True)
        stats = self.driver.get_statistics(self.context, 'HTTP_Client', 'json')
        print stats
        stats = self.driver.get_statistics(self.context, 'Test_Client', 'csv')
        print stats

    def negative_tests(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        assert(len(reservation_ports) == 2)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', '')
        self.driver.load_config(self.context, os.path.dirname(__file__).replace('\\', '/') + '/test_config.rxf')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.rxf')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Traffic1@Network1')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.rxf')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.rxf')

if __name__ == '__main__':
    sys.exit(unittest.main())
