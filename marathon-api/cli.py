#!/usr/bin/env python

#import krux.cli
import krux.logging
import sys
import socket
import json
from pprint import pprint
from marathon import MarathonClient
from marathon.models import MarathonApp
from krux.cli import Application, get_group, get_parser


class MarathonClientApp(Application):

    def __init__(self):
        super(MarathonClientApp, self).__init__(name='marathonclientapp', syslog_facility='local0')
        self.marathon_host = self.args.host
        self.marathon_port = self.args.port
        self.marathon_list_apps = self.args.list_apps
        self.marathon_config_file = self.args.config_file

    def add_cli_arguments(self, parser):
        super(MarathonClientApp, self).add_cli_arguments(parser)
        group = get_group(parser, self.name)

        group.add_argument(
            '--host',
            default='localhost',
            help='Marthon server host name or IP address. ',
        )
        group.add_argument(
            '--port',
            default='8080',
            help='Marthon server port. ',
        )
        group.add_argument(
            '--list_apps',
            action='store_true',
            default=False,
            help='Use flag to list all marathon apps. ',
        )
        group.add_argument(
            '--config_file',
            #default=False,
            help='Marathon config file to configure app. ',
        )
        group.add_argument(
            '--app',
            default=False,
            help='app flag can be used to pass an app name to get '
            'more detailed info on a running app ',
        )

    def connect(self, address, port):
        try:
            s = socket.socket()
            s.connect((address, port))
        except Exception as e:
            self.logger.error("something's wrong with %s:%d. Exception is %s" % (address, port, e))
            sys.exit(1)
        finally:
            s.close()

    def read_config_file(self, config_file):
        print(config_file)
        ### open and load json config file
        with open(config_file) as data_file:
            data = json.load(data_file)
        return data

    def list_marathon_apps(self, marathon_server):
        current_marathon_apps = marathon_server.list_apps()
        self.logger.info(current_marathon_apps)
        print(current_marathon_apps)

    def get_marathon_app(self, marathon_server, marathon_app):
        # TODO test if attributes exist
        # TODO update attributes
        try:
            marathon_app_result = marathon_server.get_app(marathon_app)
        except Exception as e:
            self.logger.error("App doesn't exist %s. Exception is %s" % (marathon_app, e))
            # TODO create new app instead of system exit
            sys.exit(1)

        marathon_app_id = marathon_server.get_app(marathon_app).id

        print(marathon_app_id)
        return marathon_app_result

    def update_marathon_app(self, marathon_server, config_file_data, marathon_app_result):
        marathon_app_result.cpus = config_file_data["cpus"]
        marathon_app_result.instances = config_file_data["instances"]
        marathon_app_result.disk = config_file_data["disk"]
        marathon_server.update_app(config_file_data["id"], marathon_app_result, force=False, minimal=True)

    def run_app(self):
        marathon_server = MarathonClient("http://" + self.marathon_host + ":" + self.marathon_port)
        # TODO command line argument
        #marathon_app = '/bash/nc-listen-test'

        ### validate socket connection with given host and port
        self.connect(self.marathon_host, int(self.marathon_port))

        self.logger.info('host = ' + self.marathon_host)
        self.logger.info('port = ' + self.marathon_port)

        ### list all apps if flag is called
        if self.marathon_list_apps:
            self.list_marathon_apps(marathon_server)

        ### Config file load, only if we passed the flag
        if self.marathon_config_file:
            config_file_data = self.read_config_file(self.marathon_config_file)

            ### get a specific marathon app
            marathon_app_result = self.get_marathon_app(marathon_server, config_file_data["id"])
            self.logger.info(marathon_app_result)

            ### update a marathon app
            self.update_marathon_app(marathon_server, config_file_data, marathon_app_result)

        ### TODO if we didn't pass a file, check to see if an app name was passed
        elif self.args.app:
            print(self.args.app)


        ### TESTS
        # pprint(data)
        # print data["cpus"]


def main():
    app = MarathonClientApp()
    app.run_app()

# Run the application stand alone
if __name__ == '__main__':
    main()
