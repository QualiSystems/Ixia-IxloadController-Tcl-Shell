
from cloudshell.traffic.driver import TrafficControllerDriver

from ixl_handler import IxlHandler


class IxLoadControllerDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = IxlHandler()

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

    #
    # Hidden commands for developers only.
    #

    def get_session_id(self, context):
        """ Returns the REST session ID.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        return self.handler.get_session_id()

    def get_children(self, context, obj_ref, child_type):
        """ Returns all children of object.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid IxLoad object reference.
        :param childr_type: requested children type.
        :return: list of children.
        """

        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context, obj_ref):
        """ Returns all children of object.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid IxLoad object reference.
        :return: list of <attribute, value>.
        """

        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """ Set object attribute.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid IxLoad object reference.
        :param attr_name: IxNetwork attribute name.
        :param attr_value: IxNetwork attribute value.
        """

        self.handler.set_attribute(obj_ref, attr_name, attr_value)
