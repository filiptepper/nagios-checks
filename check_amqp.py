#!/usr/bin/python

# REQUIREMENTS
# - py-amqplib

import sys, os, socket, struct
from amqplib import client_0_8 as amqp
from optparse import OptionParser

# Constants
EXIT_NAGIOS_OK = 0
EXIT_NAGIOS_WARN = 1
EXIT_NAGIOS_CRITICAL = 2

# Command line options
opt_parser = OptionParser()
opt_parser.add_option("-s", "--server", dest="server", help="AMQP server to connect to.")
opt_parser.add_option("-v", "--vhost", dest="vhost", help="Virtual host to log on to. (Default: /)")
opt_parser.add_option("-q", "--queue", dest="queue_name", help="Queue name to check.")
opt_parser.add_option("-d", "--durable", action="store_true", dest="durable", default="False", help="Declare queue as durable. (Default: True)")
opt_parser.add_option("-a", "--auto-delete", action="store_true", dest="auto_delete", default="False", help="Declare queue as auto-delete. (Default: False)")
opt_parser.add_option("-w", "--warn", dest="warn_threshold", help="Number of messages that triggers a warning status.")
opt_parser.add_option("-c", "--critical", dest="critical_threshold", help="Number of messages that triggers a critical status.")

args = opt_parser.parse_args()[0]

if args.server == None:
  print "An AMQP server (--server) must be supplied. Please see --help for more details."
  sys.exit(-1)

if args.vhost == None:
  args.vhost = "/"

if args.queue_name == None:
  print "A queue name (--queue) must be supplied. Please see --help for more details."
  sys.exit(-1)

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
  amqp_connection = amqp.Connection(host=args.server, virtual_host=args.vhost)
  amqp_channel = amqp_connection.channel()
  queue_info = amqp_channel.queue_declare(queue=args.queue_name, durable=args.durable, auto_delete=args.auto_delete, passive=True)
except (socket.error, amqp.AMQPConnectionException, amqp.AMQPChannelException), e:
  print "CRITICAL: Problem establishing AMQP connection to server %s: %s " % (str(args.server), str(repr(e)))
  sys.exit(EXIT_NAGIOS_CRITICAL)
except struct.error, e:
  print "CRITICAL: Authentication error connecting to vhost '%s' on server '%s'." % (str(args.vhost), str(args.server))
  sys.exit(EXIT_NAGIOS_CRITICAL)

amqp_connection.close()

# Queue information
if int(queue_info[1]) >= critical_threshold:
  print "CRITICAL: %s messages in queue '%s' on vhost '%s', server '%s'." % (str(queue_info[1]), args.queue_name, str(args.vhost), str(args.server))
  sys.exit(EXIT_NAGIOS_CRITICAL)
elif int(queue_info[1]) >= warn_threshold:
  print "WARN: %s messages in queue '%s' on vhost '%s', server '%s'." % (str(queue_info[1]), args.queue_name, str(args.vhost), str(args.server))
  sys.exit(EXIT_NAGIOS_WARN)
else:
  print "OK: %s messages in queue '%s' on vhost '%s', server '%s'." % (str(queue_info[1]), args.queue_name, str(args.vhost), str(args.server))
  sys.exit(EXIT_NAGIOS_OK)