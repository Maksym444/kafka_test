#!/bin/bash
function gracefulShutdown {
  echo "Shutting down!"
  touch CLEAN
  python -c "open('__CLEAN__', 'w+').write('test')"
  python cleanup_on_exit.py
}
trap gracefulShutdown SIGTERM
trap gracefulShutdown SIGINT
#trap gracefulShutdown SIGSTOP
#trap gracefulShutdown SIGKILL
exec "$@" &
wait
