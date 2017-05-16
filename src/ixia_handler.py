import logging
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.driver_context import AutoLoadDetails
from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixload.ixl_app import IxlApp
from ixload.api.ixl_tcl import IxlTclWrapper
from ixload.ixl_statistics_view import IxlStatView
from helper.quali_rest_api_helper import create_quali_api_instance
import re
import json
import csv
import io
import sys
import os
from os import path
from distutils.dir_util import copy_tree


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


class IxiaHandler(object):

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

    def get_inventory(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        return AutoLoadDetails([], [])

    def get_api(self, context):
        """

        :param context:
        :return:
        """

        return CloudShellSessionContext(context).get_api()

    def load_config(self, context, ixia_config_file_name):
        """
        :param str stc_config_file_name: full path to STC configuration file (tcc or xml)
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixl.load_config(ixia_config_file_name)
        repository = self.ixl.repository
        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        response = my_api.GetReservationDetails(reservationId=reservation_id)

        search_chassis = "Ixia Chassis"
        search_port = "Port"
        chassis_objs_dict = dict()
        ports_obj = []

        for resource in response.ReservationDescription.Resources:
            if resource.ResourceModelName == search_chassis:
                chassis_objs_dict[resource.FullAddress] = {'chassis': resource, 'ports': list()}
        for resource in response.ReservationDescription.Resources:
            if resource.ResourceFamilyName == search_port:
                chassis_adr = resource.FullAddress.split('/')[0]
                if chassis_adr in chassis_objs_dict:
                    chassis_objs_dict[chassis_adr]['ports'].append(resource)
                    ports_obj.append(resource)

        ports_obj_dict = dict()
        for port in ports_obj:
            val = my_api.GetAttributeValue(resourceFullPath=port.Name, attributeName="Logical Name").Value
            if val:
                port.logic_name = val
                ports_obj_dict[val.strip()] = port
        if not ports_obj_dict:
            self.logger.error("You should add logical name for ports")
            raise Exception("You should add logical name for ports")

        for port_name in ports_obj_dict:
            FullAddress = re.sub(r'PG.*?[^a-zA-Z0-9 ]', r'', ports_obj_dict[port_name].FullAddress)
            physical_add = re.sub(r'[^./0-9 ]', r'', FullAddress)
            self.logger.info("Logical Port %s will be reserved now on Physical location %s" %
                             (str(port_name), str(physical_add)))
            repository.get_object_by_name(port_name).reserve(str(physical_add))

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
        my_api = self.get_api(context)
        if output_file.lower() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            my_api.WriteMessageToReservationOutput(reservation_id, statistics_str)
            return json.loads(statistics_str)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, stats_obj.captions)
            w.writeheader()
            for time_stamp in statistics:
                w.writerow(statistics[time_stamp])
            my_api.WriteMessageToReservationOutput(reservation_id, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON')

    def get_results(self, context, client_stats, view_name):

        csvfile = open(path.join(client_stats.results_dir.replace('\\', '/'), view_name + '.csv'), 'rb')
        quali_api_helper = create_quali_api_instance(context, self.logger)
        quali_api_helper.login()
        quali_api_helper.upload_file(context.reservation.reservation_id, file_name="file_name",
                                     file_stream=csvfile)

        return "Please check attachments for results"
