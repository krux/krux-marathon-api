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

from marathon.models import MarathonApp

#
# Internal libraries
#

import krux.logging


class KruxMarathonClient(object):
    
    ATTRIBUTES_TO_SKIP = ['upgrade_strategy', 'unreachable_strategy', 'health_checks', 'ports']
    
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

    def assign_config_data(self, new_data, old_object):
        ### value for if there is a change in our json file from server values
        changes_in_json = False

        ### iterate through the values that are OK to update (according to marathon-python)
        ### and if there are changes flip the changes flag
        new_object = MarathonApp().from_json(new_data)
        check_attrs = MarathonApp.UPDATE_OK_ATTRIBUTES
        ### strip the version because that one changes every time
        if 'version' in check_attrs:
            check_attrs.remove('version')
        ### Not sure why gpus get defaulted to None, re-setting to 0
        if not new_object.gpus:
            new_object.gpus = 0
        for k in sorted(check_attrs):
            ### Try to fetch attributes from both objects
            new_attr = getattr(new_object, k)
            old_attr = getattr(old_object, k)
            if k in KruxMarathonClient.ATTRIBUTES_TO_SKIP:
                self.logger.debug("Attribute dictionaries cannot be checked for equality <<%s>>" % k)
            elif new_attr == old_attr:
                self.logger.debug("%s: <<%s>> is equal to <<%s>>" % (k, old_attr, new_attr))
            else:
                self.logger.debug("%s: updating <<%s>> to <<%s>>" % (k, old_attr, new_attr))
                ### if at least one attribute changes, flip the flag
                changes_in_json = True
        ### special case for ports: if you send both to the marathon api, it will return a 500,
        ### so you gotta pick one over the other. Usually the port_definitions will be more
        ### complete, so that's what we're going with.
        if getattr(new_object, 'port_definitions', None) and getattr(new_object, 'ports', None):
            self.logger.warn('Both port and port_definitions are set, using port_definitions only')
            new_object.ports = []
        return changes_in_json, new_object

    def get_marathon_apps(self, marathon_server):
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
        marathon_server.delete_app(marathon_app, force=True)
        self.logger.info("Marathon app deleted.")
