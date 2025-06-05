#!/bin/sh
export LD_LIBRARY_PATH="$SNAP/usr/lib/x86_64-linux-gnu/pulseaudio:$LD_LIBRARY_PATH"
exec "$@"