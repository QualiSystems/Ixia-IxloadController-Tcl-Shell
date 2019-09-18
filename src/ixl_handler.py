
import json
import csv
import io
import sys
import os
from distutils.dir_util import copy_tree
from collections import OrderedDict

from cloudshell.traffic.handler import TrafficHandler
from cloudshell.traffic.tg_helper import (get_reservation_resources, get_address, is_blocking, attach_stats_csv,
                                          get_family_attribute)

from trafficgenerator.tgn_utils import ApiType
from ixload.ixl_app import init_ixl
from ixload.ixl_statistics_view import IxlStatView

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext


class IxlHandlerTcl(TrafficHandler):

    def initialize(self, context, logger):

        self.logger = logger

        client_install_path = context.resource.attributes['Client Install Path'].replace('\\', '/')
        if sys.platform == 'win32':
            self._windows_tcl_env(client_install_path)

        self.ixl = init_ixl(ApiType.tcl, self.logger, client_install_path)

        address = context.resource.attributes['Controller Address']
        if not address:
            address = 'localhost'
        self.logger.info('connecting to address {}'.format(address))
        self.ixl.connect(ip=address)
        if sys.platform == 'win32':
            log_file_name = self.logger.handlers[0].baseFilename
            self.server_results_dir = (os.path.splitext(log_file_name)[0] + '--Results').replace('\\', '/')
            self.client_results_dir = self.server_results_dir
        else:
            self.server_results_dir = 'c:/IxLoadResults'
            self.client_results_dir = '/IxLoadResults'
        logger.info('results directory = ' + self.server_results_dir)
        self.ixl.controller.set_results_dir(self.server_results_dir)
        self.logger.info("Port Reservation Completed")

    def tearDown(self):
        self.ixl.disconnect()

    def load_config(self, context, ixia_config_file_name):

        self.ixl.load_config(ixia_config_file_name)
        self.ixl.repository.test.set_attributes(enableForceOwnership=False)
        config_elements = self.ixl.repository.get_elements()

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = {}
        for port in get_reservation_resources(my_api, context.reservation.reservation_id,
                                              'Generic Traffic Generator Port',
                                              'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                              'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort'):
            reservation_ports[get_family_attribute(my_api, port, 'Logical Name').Value.strip()] = port

        perfectstorms = [ps.FullAddress for ps in get_reservation_resources(my_api, reservation_id,
                                                                            'PerfectStorm Chassis Shell 2G')]

        for name, element in config_elements.items():
            if name in reservation_ports:
                address = get_address(reservation_ports[name])
                ip_address, module, port = address.split('/')
                if ip_address in perfectstorms:
                    address = '{}/{}/{}'.format(ip_address, module, int(port) + 1)
                self.logger.debug('Logical Port {} will be reserved on Physical location {}'.format(name, address))
                element.reserve(address)
            else:
                self.logger.error('Configuration element "{}" not found in reservation elements {}'.
                                  format(element, reservation_ports.keys()))
                raise Exception('Configuration element "{}" not found in reservation elements {}'.
                                format(element, reservation_ports.keys()))

        self.logger.info("Port Reservation Completed")

    def start_test(self, blocking):
        self.ixl.start_test(is_blocking(blocking))

    def stop_test(self):
        self.ixl.stop_test()

    def get_statistics(self, context, view_name, output_type):

        stats_obj = IxlStatView(view_name, self.client_results_dir)
        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, ['Timestamp'] + stats_obj.captions)
            w.writeheader()
            for time_stamp in statistics:
                w.writerow(OrderedDict({'Timestamp': time_stamp}.items() + statistics[time_stamp].items()))
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))

    #
    # Private auxiliary methods.
    #

    def _windows_tcl_env(self, client_install_path):
        self.logger.info('Copy reg1.2 to Tcl')
        ixia_tcl_reg_path = client_install_path + '/3rdParty/Python2.7/Lib/tcl8.5/reg1.2'
        python_interpreter_path = sys.executable.replace('\\', '/').rstrip('Scripts/python.exe')
        python_tcl_reg_path = python_interpreter_path + "/tcl/reg1.2"
        if not (os.path.isdir(python_tcl_reg_path)):
            copy_tree(ixia_tcl_reg_path, python_tcl_reg_path)
