
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from ixl_handler import IxlHandler
import tg_helper


class IxLoadControllerDriver(ResourceDriverInterface):

    def __init__(self):
        self.handler = IxlHandler()

    def initialize(self, context):
        """
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.initialize(context)

    def load_config(self, context, ixl_config_file_name):
        """ Load IxLoad configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixl_config_file_name: full path to IxLoad configuration file (rxf).
        """

        tg_helper.enqueue_keep_alive(context)
        self.handler.load_config(context, ixl_config_file_name)
        return ixl_config_file_name + ' loaded, ports reserved'

    def start_test(self, context, blocking):
        """ Start IxLoad test.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param blocking: True - wait until test ends, False - start test and return immediately.
        """

        self.handler.start_test(blocking)

    def stop_test(self, context):
        """ Stop IxLoad test.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_test()

    def get_statistics(self, context, view_name, output_type):
        """ Get statistics for specific view.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: requested statistics view name.
        :param output_type: JSON/CSV.
        """

        return self.handler.get_statistics(context, view_name, output_type)

    def cleanup(self):
        self.handler.tearDown()

    def keep_alive(self, context, cancellation_context):

        while not cancellation_context.is_cancelled:
            pass
        if cancellation_context.is_cancelled:
            self.handler.tearDown()
