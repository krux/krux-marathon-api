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


class KruxMarathonClient(object):
    def __init__(self):

        NAME = 'KruxMarathonClient'
        self.logger = krux.logging.get_logger(name=NAME)

    def connect(self, address, port):
        """
        Tests connecting to the Marathon Server given. Takes in a host and port.
        If the values weren't passed on the command line, defaults will be used.
        If the connection fails, the program will stop and exit with a value of 1.
        """
        self.logger.info('Testing connection to marathon server\nhost = ' + address + '\nport = ' + str(port))
        try:
            s = socket.socket()
            s.connect((address, port))
            return True
        except Exception as e:
            self.logger.error("something's wrong with %s:%d. Exception is %s", address, port, e)
            return False
            #sys.exit(1)
        finally:
            s.close()

    def read_config_file(self, config_file):
        """
        Open the json file passed on the command line. The program will stop and
        exit with a value of 1 if it cannot open or parse the json file.
        """
        self.logger.info("Reading config file and formatting data from config file :  " + config_file)
        ### open and load json config file
        try:
            with open(config_file) as data_file:
                data = json.load(data_file)
        except Exception as e:
            self.logger.error("Error in json file:  %s. Exception is %s", config_file, e)
            sys.exit(1)
        return data

    def assign_config_data(self, config_file_data, marathon_app_result):
        ### value for if there is a change in our json file from server values
        changes_in_json = False

        ### iterate through our json file's values and compare them to the values
        ### on the marathon server
        for attribute, value in config_file_data.iteritems():
            ### upgrade_strategy value returns a class an not a json, extra work
            ### needs to be done to convert this to a comparable value
            if attribute == 'upgrade_strategy':
                ### the marathon api allows us to convert this attribute to json
                marathon_app_result_original = getattr(marathon_app_result, attribute).to_json()
                value_json = json.dumps(value)
                if marathon_app_result_original == value_json:
                    self.logger.info(attribute, ': ', marathon_app_result_original, ' is equal to ', value_json)
                    pass
                else:
                    changes_in_json = True
                    setattr(marathon_app_result, attribute, value)
                    self.logger.info('Updating ', attribute, ' from \n', marathon_app_result_original, '\nto \n', value_json)
            else:
                marathon_app_result_original = getattr(marathon_app_result, attribute)
                if marathon_app_result_original == value:
                    self.logger.info(attribute, ': ', marathon_app_result_original, ' is equal to ', value)
                    pass
                else:
                    changes_in_json = True
                    setattr(marathon_app_result, attribute, value)
                    self.logger.info('Updating ', attribute, ' from \n', marathon_app_result_original, '\nto \n', value)

        ### ports and port_definitions don't play nicely together, if both are
        ### set, then use the more specific port_definitions and log a warning
        if config_file_data.get("ports") and config_file_data.get("port_definitions"):
            marathon_app_result.ports = None
            self.logger.warn('both ports and port_definitions are set, using port_definitions')
        return changes_in_json

    def list_marathon_apps(self, marathon_server):
        """
        This method connects to the marathon server and requests all the
        Marathon Apps.
        """
        self.logger.info("Listing apps running on marathon")
        current_marathon_apps = marathon_server.list_apps()
        self.logger.debug(current_marathon_apps)
        return current_marathon_apps

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
                self.logger.warn("App doesn't exist %s. Exception is %s", app_id, e)
                ### App doesn't exist; initialize it
                self.create_marathon_app(marathon_server, config_file_data)
                marathon_app_result = marathon_server.get_app(config_file_data["id"])
        else:
            try:
                marathon_app_result = marathon_server.get_app(app_id)
            except Exception as e:
                self.logger.warn("App doesn't exist %s. Exception is %s", app_id, e)
                sys.exit(1)
        return marathon_app_result

    def update_marathon_app(self, marathon_server, config_file_data, marathon_app_result):
        """
        Connects to the Marathon Server and sends the App variables. If the
        values have changed, the App will be updated on the server, otherwise
        it makes no changes.
        """
        ### API call to marathon server to update the app if the values have changed
        ### The Marathon package and server API does verification of data so no
        ### reason to recheck here.
        ### An app can be stuck in a scaling state, force=True keeps us from getting hung.
        self.logger.info("Update marathon server with updated app data")
        marathon_server.update_app(config_file_data["id"], marathon_app_result, force=True, minimal=True)

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
