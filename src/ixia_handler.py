import logging
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.driver_context import AutoLoadDetails
from trafficgenerator.tgn_tcl import TgnTkMultithread,TgnTk
from ixload.ixl_app import IxlApp
from ixload.api.ixl_tcl import IxlTclWrapper
from ixload.ixl_statistics_view import IxlStatView
from os import path
from helper.quali_rest_api_helper import create_quali_api_instance
import re
import json
import csv
import io
import sys
from distutils.dir_util import copy_tree

class IxiaHandler(object):

    def initialize(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.InitCommandContext
        """
        #os.system("set TCL_LIBRARY=C:/Program Files (x86)/Ixia/Tcl/8.5.17.0/lib/tcl8.5")
        #os.system("set TK_LIBRARY=C:/Program Files (x86)/Ixia/Tcl/8.5.17.0/lib/tk8.5")
        client_install_path = context.resource.attributes['Client Install Path']
        client_install_path = client_install_path.replace('\\','/')
        python_interpreter_path = sys.executable.rstrip("\\Scripts\\python.exe")
        src_path = client_install_path.rsplit('Ixia/', 1)[0]
        copy_tree(src_path + "Ixia\\Tcl\\8.5.17.0\\lib\\tcl8.5\\reg1.2", python_interpreter_path + "\\tcl\\tcl8.5\\reg1.2")

        log_file = 'ixload_shell_logger.txt'

        self.logger = logging.getLogger('root')
        self.logger.addHandler(logging.FileHandler(log_file))
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


    def stop_test(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixl.stop_test()

    def start_test(self, context,blocking):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        blocking = bool(blocking) if blocking in ["true", "True"] else False
        self.ixl.start_test(blocking)

    def get_statistics(self, context, view_name, output_type):

        output_file = output_type.lower().strip()
        if output_file != 'json' and output_file != 'csv':
            raise Exception("The output format should be json or csv")
        client_stats = IxlStatView(view_name)
        client_stats.read_stats()
        statistics = client_stats.statistics
        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        if output_file.lower() == 'json':
            statistics = json.dumps(statistics, indent=4, sort_keys=True,ensure_ascii=False)
            my_api.WriteMessageToReservationOutput(reservation_id, statistics)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, statistics.keys())
            w.writeheader()
            w.writerow(statistics)
            my_api.WriteMessageToReservationOutput(reservation_id,output.getvalue().strip('\r\n'))
        #self.upload_file_to_reservation(context,my_api,reservation_id)
        self.get_results(context,client_stats,view_name)



    def get_results(self,context,client_stats,view_name):


        csvfile = open(path.join(client_stats.results_dir.replace('\\', '/'), view_name + '.csv'), 'rb')#open('ixload_stats.csv')
        quali_api_helper = create_quali_api_instance(context, self.logger)
        quali_api_helper.login()
        quali_api_helper.upload_file(context.reservation.reservation_id, file_name="file_name",
                                     file_stream=csvfile)
        #with open(save_file_name, 'w') as result_file:
        #    result_file.write(pdf_result)

        return "Please check attachments for results"