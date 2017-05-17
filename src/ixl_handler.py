
import logging
import json
import csv
import io
import sys
import os
import time
from distutils.dir_util import copy_tree
from collections import OrderedDict

from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixload.ixl_app import IxlApp
from ixload.api.ixl_tcl import IxlTclWrapper
from ixload.ixl_statistics_view import IxlStatView

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from helper.quali_rest_api_helper import create_quali_api_instance


def get_reservation_ports(session, reservation_id):
    """ Get all Generic Traffic Generator Port in reservation.

    :return: list of all Generic Traffic Generator Port resource objects in reservation
    """

    reservation_ports = []
    reservation = session.GetReservationDetails(reservation_id).ReservationDescription
    for resource in reservation.Resources:
        if resource.ResourceModelName == 'Generic Traffic Generator Port':
            reservation_ports.append(resource)
    return reservation_ports


class IxlHandler(object):

    def initialize(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.InitCommandContext
        """

        client_install_path = context.resource.attributes['Client Install Path'].replace('\\', '/')
        ixia_tcl_reg_path = client_install_path + '/3rdParty/Python2.7/Lib/tcl8.5/reg1.2'
        python_interpreter_path = sys.executable.replace('\\', '/').rstrip('Scripts/python.exe')
        python_tcl_reg_path = python_interpreter_path + "/tcl/reg1.2"
        if not (os.path.isdir(python_tcl_reg_path)):
            copy_tree(ixia_tcl_reg_path, python_tcl_reg_path)

        self.logger = logging.getLogger('ixload')
        self.logger.addHandler(logging.FileHandler('c:/temp/ixload_shell_logger.txt'))
        self.logger.setLevel('DEBUG')

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        api_wrapper = IxlTclWrapper(self.logger, client_install_path, self.tcl_interp)
        self.ixl = IxlApp(self.logger, api_wrapper)

        address = context.resource.address

        self.logger.info("connecting to address {}".format(address))
        self.ixl.connect(ip=address)
        self.logger.info("Finished connecting to address {}".format(address))
        return ""

    def tearDown(self):
        self.tcl_interp.stop()

    def load_config(self, context, ixia_config_file_name):
        """
        :param str stc_config_file_name: full path to STC configuration file (tcc or xml)
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixl.load_config(ixia_config_file_name)
        config_elements = self.ixl.repository.get_elements()

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = {}
        for port in get_reservation_ports(my_api, reservation_id):
            reservation_ports[my_api.GetAttributeValue(port.Name, 'Logical Name').Value.strip()] = port

        for name, element in config_elements.items():
            if name in reservation_ports:
                address = reservation_ports[name].FullAddress
                self.logger.debug('Logical Port {} will be reserved on Physical location {}'.format(name, address))
                element.reserve(address)
            else:
                self.logger.error('Configuration element "{}" not found in reservation elements {}'.
                                  format(element, reservation_ports.keys()))
                raise Exception('Configuration element "{}" not found in reservation elements {}'.
                                format(element, reservation_ports.keys()))

        self.logger.info("Port Reservation Completed")

    def start_test(self, context, blocking):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixl.start_test(bool(blocking))

    def stop_test(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixl.stop_test()

    def get_statistics(self, context, view_name, output_type):

        output_file = output_type.lower().strip()
        if output_file != 'json' and output_file != 'csv':
            raise Exception("The output format should be json or csv")
        stats_obj = IxlStatView(view_name)
        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()
        if output_file.lower() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, ['Timestamp'] + stats_obj.captions)
            w.writeheader()
            for time_stamp in statistics:
                w.writerow(OrderedDict({'Timestamp': time_stamp}.items() + statistics[time_stamp].items()))
            quali_api_helper = create_quali_api_instance(context, self.logger)
            quali_api_helper.login()
            full_file_name = view_name.replace(' ', '_') + '_' + time.ctime().replace(' ', '_') + '.csv'
            quali_api_helper.upload_file(context.reservation.reservation_id,
                                         file_name=full_file_name,
                                         file_stream=output.getvalue().strip())
            my_api.WriteMessageToReservationOutput(reservation_id,
                                                   'Statistics view saved in attached file - ' + full_file_name)
            return output.getvalue().strip('\r\n')
        else:
            raise Exception('Output type should be CSV/JSON')
