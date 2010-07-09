nagios-checks
=============

Both are prepared for Nagios, but you can run them as-is.

Redis
-----

Checks whether host is up and responding and checks for memory usage.

Requires `redis-py` installed.

Example:

    ./check_redis.py --server redis.host --warn 2048 --critical 4096 --rss-warn 3000 --rss-critical 5000

Both `--warn` and `--critical` params are in megabytes.

AMQP
----

Checks whether host is up and responding and checks the queue size.

Requires `py-amqplib` installed.

Example:

    ./check_amqp.py --server amqp.host --queue messages --warn 1000 --critical 10000