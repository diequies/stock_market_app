#!/bin/bash
# Export environment variables for cron jobs
printenv | grep -v "no_proxy" >> /etc/environment

# Start cron in the foreground
cron -f