#!/usr/bin/env python

#
# Standard libraries
#

from __future__ import absolute_import
import json
import os
import sys

#
# Third party libraries
#

from marathon import MarathonClient
from marathon.util import MarathonJsonEncoder

#
# Internal libraries
#

from krux.cli import Application, get_group
import krux_marathon_api.marathonapi


class MarathonCliApp(Application):

    def __init__(self):
        super(MarathonCliApp, self).__init__(name='marathon_cli', syslog_facility='local0')
        self.api = krux_marathon_api.marathonapi.KruxMarathonClient()
        self.marathon_host = self.args.host
        self.marathon_port = self.args.port
        self.marathon_user = self.args.username
        self.marathon_pass = self.args.password
        self.marathon_list_apps = self.args.list_apps
        self.json = self.args.json
        if self.args.config_file:
            ### Handles files passed via i.e. ~/some-link.json and it will translate
            ### to the proper full location
            self.marathon_config_file = os.path.realpath(
                os.path.expanduser(self.args.config_file)
            )
        else:
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
            '--username',
            default=os.getenv('MARATHON_HTTP_USERNAME'),
            help='Marathon server username (default: %(default)s)'
        )
        group.add_argument(
            '--password',
            default=os.getenv('MARATHON_HTTP_PASSWORD'),
            help='Marathon server password (default: %(default)s)'
        )
        group.add_argument(
            '--list-apps',
            action='store_true',
            default=False,
            help='Use flag to list all marathon apps. ',
        )
        group.add_argument(
            '--config-file',
            default=None,
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
        group.add_argument(
            '--json',
            action='store_true',
            default=False,
            help='Show output in JSON format'
        )

    def run_app(self):
        """
        Creates the Marathon Server connection.
        When using json config files, the tool is used to ensure state of the App.
        If the App doesn't exist, it tries to create it.
        This tool can also be used to delete Apps from Marathon via either a
        json config file or using the App name from the command line.
        """

        ### if not a single modifier is specified, show the usage string instead
        ### of segfaulting
        if not any([
            self.args.list_apps,
            self.args.config_file,
            self.args.get_app,
            self.args.delete,
        ]):
            self.parser.print_help()
            self.parser.exit()

        server_str = "http://" + self.marathon_host + ":" + self.marathon_port
        marathon_server = MarathonClient(
            server_str,
            username=self.marathon_user,
            password=self.marathon_pass,
        )

        ### validate socket connection with given host and port
        if self.api.connect(self.marathon_host, int(self.marathon_port)):
            self.logger.info('Connection success')
        else:
            self.logger.error('Error connecting to Server')
            raise IOError('Error connecting to Server')

        ### list all apps if flag is called
        if self.marathon_list_apps:
            apps = self.api.get_marathon_apps(marathon_server)
            if self.json:
                # the JSON encoder in marathon.util recursively translates all
                # items into JSON friendly structures
                print(
                    json.dumps(
                        apps,
                        cls=MarathonJsonEncoder,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '),
                    )
                )
            else:
                for app in apps:
                    print('{0} => {1}'.format(app.id, app.cmd))

        ### Config file load, only if we passed the variable
        if self.marathon_config_file:
            config_file_data = self.api.read_config_file(self.marathon_config_file)

            # make it possible to load more than 1 app from a single source file
            if isinstance(config_file_data, dict):
                self.logger.debug('found a single app definition in config file')
                apps = [config_file_data]
            elif isinstance(config_file_data, list):
                self.logger.debug('found a list of app definitions in config file')
                apps = config_file_data
            else:
                raise ValueError('Input config file appears to be in the wrong format')

            for app in apps:
                ### get a specific marathon app
                marathon_app_result = self.api.get_marathon_app(marathon_server, app, app["id"])
                self.logger.info('marathon app before updates: ')
                self.logger.info(marathon_app_result)

                ### update local app data variable with config file values
                changes_in_json, new_marathon_app = self.api.assign_config_data(app, marathon_app_result)

                ### update a marathon app if there was a change in the json file
                if changes_in_json:
                    self.logger.info('marathon app after updates: ')
                    self.api.update_marathon_app(marathon_server, app, new_marathon_app)

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
    sys.exit(app.run_app())


# Run the application stand alone
if __name__ == '__main__':
    main()
