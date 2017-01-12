#!/usr/bin/env python

#
# Standard libraries
#

from __future__ import absolute_import

#
# Third party libraries
#

from marathon import MarathonClient
from marathon.models import MarathonApp

#
# Internal libraries
#

import krux.logging
from krux.cli import Application, get_group, get_parser
import krux_marathon_api.marathonapi


class MarathonCliApp(Application):

    def __init__(self):
        super(MarathonCliApp, self).__init__(name='marathon_cli', syslog_facility='local0')
        self.api = krux_marathon_api.marathonapi.KruxMarathonClient()
        self.marathon_host = self.args.host
        self.marathon_port = self.args.port
        self.marathon_list_apps = self.args.list_apps
        self.marathon_config_file = self.args.config_file
        self.marathon_get_app = self.args.get_app
        self.marathon_delete = self.args.delete

    def add_cli_arguments(self, parser):
        """
        Adds command line arguments, these options can be seen using -h when calling the app.
        """
        super(MarathonCliApp, self).add_cli_arguments(parser)
        group = get_group(parser, self.name)

        group.add_argument(
            '--host',
            default='localhost',
            help='Marathon server host name or IP address. ',
        )
        group.add_argument(
            '--port',
            default='8080',
            help='Marathon server port. ',
        )
        group.add_argument(
            '--list-apps',
            action='store_true',
            default=False,
            help='Use flag to list all marathon apps. ',
        )
        group.add_argument(
            '--config-file',
            default=False,
            help='Marathon config file to configure app. ',
        )
        group.add_argument(
            '--get-app',
            default=False,
            help='app flag can be used to pass an app name to get '
            'more detailed info on a running app ',
        )
        group.add_argument(
            '--delete',
            action='store_true',
            default=False,
            help='Set flag to delete an app '
        )

    def run_app(self):
        """
        Creates the Marathon Server connection.
        When using json config files, the tool is used to ensure state of the App.
        If the App doesn't exist, it tries to create it.
        This tool can also be used to delete Apps from Marathon via either a
        json config file or using the App name from the command line.
        """
        marathon_server = MarathonClient("http://" + self.marathon_host + ":" + self.marathon_port)

        ### validate socket connection with given host and port
        self.api.connect(self.marathon_host, int(self.marathon_port))

        ### list all apps if flag is called
        if self.marathon_list_apps:
            current_marathon_apps = self.api.list_marathon_apps(marathon_server)
            self.logger.info(current_marathon_apps)

        ### Config file load, only if we passed the variable
        if self.marathon_config_file:
            config_file_data = self.api.read_config_file(self.marathon_config_file)

            ### get a specific marathon app
            marathon_app_result = self.api.get_marathon_app(marathon_server, config_file_data, config_file_data["id"])
            self.logger.info(marathon_app_result)

            ### update app data variable with config file values
            self.api.assign_config_data(config_file_data, marathon_app_result)

            ### update a marathon app
            self.api.update_marathon_app(marathon_server, config_file_data, marathon_app_result)

        elif self.args.get_app:
            self.logger.info(self.args.get_app)
            config_file_data = None
            marathon_app_result = self.api.get_marathon_app(marathon_server, config_file_data, self.args.get_app)
            self.logger.info(marathon_app_result)

        ### Delete marathon app
        if self.args.delete:
            self.api.delete_marathon_app(marathon_server, marathon_app_result.id)
            self.logger.info('Deleting app')


def main():
    app = MarathonCliApp()
    app.run_app()

# Run the application stand alone
if __name__ == '__main__':
    main()
