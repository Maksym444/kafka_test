#!/bin/bash
function gracefulShutdown {
  echo "Shutting down!"
  python cleanup_on_exit.py
}
trap gracefulShutdown SIGTERM
trap gracefulShutdown SIGINT
#trap gracefulShutdown SIGSTOP
#trap gracefulShutdown SIGKILL
exec "$@" &
wait
