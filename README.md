# krux-marathon-api

This is a command line tool to help create, delete, and keep Marathon apps in a specified state.
It comes with a sample json config file for specifying state of an app.

The Application defaults to localhost and port 8080 use the host and port flags to change the location.

```./cli.py --host marathon_server.com --port 8081 --list_apps```

## Create / Update Marathon Application
Requires a valid json file (see sample).

```./cli.py --config_file ../bash_nc_listen_sample.json```

The application will connect to your marathon server, look to see if an application with the same name exists. If it exists already, it will update the app with the values in the json config file. If the application doesn't exist, it will create it.

## Delete Marathon Application
You can delete an app using the json file or just using the app name

```./cli.py --config_file ../bash_nc_listen_sample.json --delete```

```./cli.py --get_app /bash/nc-listen-test --delete```

## List all Applications
List all applications on your Marathon Server.

```./cli.py --list_apps```

### List all available commands
Running ```marathon-api/cli.py -h ``` will show you a list of possible commands.

```
usage: cli.py [-h] [--log-level {info,debug,critical,warning,error}]
              [--log-file LOG_FILE] [--no-syslog-facility]
              [--syslog-facility SYSLOG_FACILITY] [--no-log-to-stdout]
              [--stats] [--stats-host STATS_HOST] [--stats-port STATS_PORT]
              [--stats-environment STATS_ENVIRONMENT] [--lock-dir LOCK_DIR]
              [--host HOST] [--port PORT] [--list_apps]
              [--config_file CONFIG_FILE] [--get_app APP] [--delete]

marathonclientapp

optional arguments:
  -h, --help            show this help message and exit

logging:
  --log-level {info,debug,critical,warning,error}
                        Verbosity of logging. (default: warning)
  --log-file LOG_FILE   Full-qualified path to the log file (default: None).
  --no-syslog-facility  disable syslog facility
  --syslog-facility SYSLOG_FACILITY
                        syslog facility to use (default: local7).
  --no-log-to-stdout    Suppress logging to stdout/stderr (default: True).

stats:
  --stats               Enable sending statistics to statsd. (default: False)
  --stats-host STATS_HOST
                        Statsd host to send statistics to. (default:
                        localhost)
  --stats-port STATS_PORT
                        Statsd port to send statistics to. (default: 8125)
  --stats-environment STATS_ENVIRONMENT
                        Statsd environment. (default: dev)

lockfile:
  --lock-dir LOCK_DIR   Dir where lock files are stored (default: /tmp)

marathonclientapp:
  --host HOST           Marathon server host name or IP address.
  --port PORT           Marathon server port.
  --list_apps           Use flag to list all marathon apps.
  --config_file CONFIG_FILE
                        Marathon config file to configure app.
  --get_app APP         app flag can be used to pass an app name to get more
                        detailed info on a running app
  --delete              Set flag to delete an app
```
