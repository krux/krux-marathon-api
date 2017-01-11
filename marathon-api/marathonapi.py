#!/usr/bin/env python

#
# Standard libraries
#

from __future__ import absolute_import
import sys
import socket
import json

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


class Api(object):
    #VERSION = 0.1

    def __init__(self):

        NAME = 'marathonapi'
        self.logger = krux.logging.get_logger(name=NAME)

    def connect(self, address, port):
        """
        Tests connecting to the Marathon Server given. Takes in a host and port.
        If the values weren't passed on the command line, defaults will be used.
        If the connection fails, the program will stop and exit with a value of 1.
        """
        self.logger.info("Testing connection to marathon server")
        self.logger.info('host = ' + address)
        self.logger.info('port = ' + str(port))

        try:
            s = socket.socket()
            s.connect((address, port))
        except Exception as e:
            self.logger.error("something's wrong with %s:%d. Exception is %s" % (address, port, e))
            sys.exit(1)
        finally:
            s.close()

    def read_config_file(self, config_file):
        """
        Open the json file passed on the command line. The program will stop and
        exit with a value of 1 if it cannot open or parse the json file.
        """
        self.logger.info("Reading config file and formatting data.")
        self.logger.info(config_file)
        ### open and load json config file
        try:
            with open(config_file) as data_file:
                data = json.load(data_file)
        except Exception as e:
            self.logger.error("Error in json file:  %s. Exception is %s" % (config_file, e))
            sys.exit(1)
        return data

    def assign_config_data(self, config_file_data, marathon_app_result):
        """
        Assign variables from the config file to the marathon app values.
        We cannot use a dymnamic variable so we are assigning these one at a time.
        """
        ### assigning values from json to our marathon app
        self.logger.info("Assigning json variables to app data")
        marathon_app_result.cpus                     = config_file_data["cpus"]
        marathon_app_result.mem                      = config_file_data["mem"]
        marathon_app_result.instances                = config_file_data["instances"]
        marathon_app_result.disk                     = config_file_data["disk"]
        marathon_app_result.cmd                      = config_file_data["cmd"]
        marathon_app_result.backoff_factor           = config_file_data["backoff_factor"]
        marathon_app_result.constraints              = config_file_data["constraints"]
        marathon_app_result.container                = config_file_data["container"]
        marathon_app_result.dependencies             = config_file_data["dependencies"]
        marathon_app_result.env                      = config_file_data["env"]
        marathon_app_result.executor                 = config_file_data["executor"]
        marathon_app_result.health_checks            = config_file_data["health_checks"]
        marathon_app_result.labels                   = config_file_data["labels"]
        marathon_app_result.max_launch_delay_seconds = config_file_data["max_launch_delay_seconds"]
        #marathon_app_result.ports = config_file_data["ports"]      # You cannot specify both ports and port definitions
        marathon_app_result.require_ports            = config_file_data["require_ports"]
        marathon_app_result.store_urls               = config_file_data["store_urls"]
        marathon_app_result.upgrade_strategy         = config_file_data["upgrade_strategy"]
        marathon_app_result.uris                     = config_file_data["uris"]
        marathon_app_result.user                     = config_file_data["user"]                 #updates confirmed

    def list_marathon_apps(self, marathon_server):
        """
        This method connects to the marathon server and requests all the
        Marathon Apps.
        """
        self.logger.info("Listing apps running on marathon")
        current_marathon_apps = marathon_server.list_apps()
        self.logger.info(current_marathon_apps)

    def get_marathon_app(self, marathon_server, config_file_data, app_id):
        """
        Connects to the Marathon Server using the supplied App ID.
        If we passed the config file and the App isn't found on the server, we
        try to create it.
        If the App name was passed on the command line instead, we will just
        return with an error if the App wasn't found.
        Input is marathon connection, config file data, and App id.
        Returns the Marathon App results.
        """
        self.logger.info("Getting app info from the marathon server")
        if config_file_data:
            try:
                marathon_app_result = marathon_server.get_app(app_id)
            except Exception as e:
                self.logger.warn("App doesn't exist %s. Exception is %s" % (app_id, e))
                ### App doesn't exist; initialize it
                self.create_marathon_app(marathon_server, config_file_data)
                marathon_app_result = marathon_server.get_app(config_file_data["id"])
        else:
            try:
                marathon_app_result = marathon_server.get_app(app_id)
            except Exception as e:
                self.logger.warn("App doesn't exist %s. Exception is %s" % (app_id, e))
                sys.exit(1)

        self.logger.info(marathon_app_result)
        return marathon_app_result

    def update_marathon_app(self, marathon_server, config_file_data, marathon_app_result):
        """
        Connects to the Marathon Server and sends the App variables. If the
        values have changed, the App will be updated on the server, otherwise
        it makes no changes.
        """
        ### API call to marathon server to update the app if the values have changed
        self.logger.info("Update marathon server with updated app data")
        marathon_server.update_app(config_file_data["id"], marathon_app_result, force=False, minimal=True)

    def create_marathon_app(self, marathon_server, config_file_data):
        """
        Creates the App name on the Marathon Server with minimal default values.
        """
        self.logger.info("App wasn't found. Creating new marathon app")
        self.logger.info(config_file_data["id"])

        ### Initialize app creation and name space
        marathon_server.create_app(config_file_data["id"], MarathonApp(cmd='test', mem=1, cpus=.01))
        self.logger.info("Done creating marathon app.")

    def delete_marathon_app(self, marathon_server, marathon_app):
        """
        Connects to the Marathon Server and issues a delete request.
        """
        self.logger.info("Deleting :")
        self.logger.info(marathon_app)
        marathon_server.delete_app(marathon_app)
        self.logger.info("Marathon app deleted.")
