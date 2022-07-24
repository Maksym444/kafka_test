#!/bin/bash
function gracefulShutdown {
  echo "Shutting down!"
  touch CLEANUP
  python cleanup_on_exit.py
}
trap gracefulShutdown SIGTERM
trap gracefulShutdown SIGINT
exec "$@" &
wait
