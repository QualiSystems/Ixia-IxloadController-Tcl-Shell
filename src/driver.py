
from cloudshell.traffic.driver import TrafficControllerDriver

from ixl_handler import IxlHandlerTcl


class IxLoadControllerTclDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = IxlHandlerTcl()

    def load_config(self, context, ixl_config_file_name):
        """ Load IxLoad configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixl_config_file_name: full path to IxLoad configuration file (rxf).
        """

        super(self.__class__, self).load_config(context)
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

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
