#!/usr/bin/python

# REQUIREMENTS
# - redis-py

import sys, os, socket, struct
import redis
from optparse import OptionParser

# Constants
EXIT_NAGIOS_OK = 0
EXIT_NAGIOS_WARN = 1
EXIT_NAGIOS_CRITICAL = 2

# Command line options
opt_parser = OptionParser()
opt_parser.add_option("-s", "--server", dest="server", help="Redis server to connect to.")
opt_parser.add_option("-p", "--port", dest="port", help="Redis port to connect to. (Default: 6379)")
opt_parser.add_option("-w", "--warn", dest="warn_threshold", help="Memory utlization (in MB) that triggers a warning status.")
opt_parser.add_option("-c", "--critical", dest="critical_threshold", help="Memory utlization (in MB) that triggers a critical status.")

args = opt_parser.parse_args()[0]

if args.server == None:
  print "A Redis server (--server) must be supplied. Please see --help for more details."
  sys.exit(-1)

if args.port == None:
  args.port = 6379

if args.warn_threshold == None:
  print "A warning threshold (--warn) must be supplied. Please see --help for more details."
  sys.exit(-1)

try:
  warn_threshold = int(args.warn_threshold)
  if warn_threshold < 0:
    raise ValueError
except ValueError, e:
  print "Warning threshold (--warn) must be a positive integer. Please see --help for more details."
  sys.exit(-1)

if args.critical_threshold == None:
  print "A critical threshold (--critical) must be supplied. Please see --help for more details."
  sys.exit(-1)

try:
  critical_threshold = int(args.critical_threshold)
  if critical_threshold < 0:
    raise ValueError
except ValueError, e:
  print "Critical threshold (--critical) must be a positive integer. Please see --help for more details."
  sys.exit(-1)

# ================
# = Nagios check =
# ================

# Connection
try:
  redis_connection = redis.Redis(host=args.server, port=int(args.port))
  redis_info = redis_connection.info()
except (socket.error, redis.exceptions.ConnectionError), e:
  print "CRITICAL: Problem establishing connection to Redis server %s: %s " % (str(args.server), str(repr(e)))
  sys.exit(EXIT_NAGIOS_CRITICAL)

# Redis VM
if redis_info.get("vm_conf_pages", None) != None and redis_info.get("vm_stats_used_pages", None) != None:
  if int(redis_info["vm_conf_pages"]) < int(redis_info["vm_stats_used_pages"]):
    if (float(redis_info["vm_conf_pages"]) / float(redis_info["vm_stats_used_pages"])) < 0.5:
      print "CRITICAL: Redis is using %d VM pages of %d allowed" % (int(redis_info["vm_stats_used_pages"]), int(redis_info["vm_conf_pages"]))
      sys.exit(EXIT_NAGIOS_CRITICAL)
    else:
      print "WARN: Redis is using %d VM pages of %d allowed" % (int(redis_info["vm_stats_used_pages"]), int(redis_info["vm_conf_pages"]))
      sys.exit(EXIT_NAGIOS_CRITICAL)

# Redis memory usage
if redis_info["used_memory"] / 1024 / 1024 >= critical_threshold:
  print "CRITICAL: Redis is using %dMB of RAM." % (redis_info["used_memory"] / 1024 / 1024)
  sys.exit(EXIT_NAGIOS_CRITICAL)
elif redis_info["used_memory"] / 1024 / 1024 >= warn_threshold:
  print "WARN: Redis is using %dMB of RAM." % (redis_info["used_memory"] / 1024 / 1024)
  sys.exit(EXIT_NAGIOS_WARN)
else:
  print "OK: Redis is using %dMB of RAM. Days Up: %s Clients: %s Version: %s" % \
  ( \
    redis_info["used_memory"] / 1024 / 1024,
    redis_info["uptime_in_days"],
    redis_info["connected_clients"],
    redis_info["redis_version"]
  )
  sys.exit(EXIT_NAGIOS_OK)