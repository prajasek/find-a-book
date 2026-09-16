#!/bin/sh

rm -f /tmp/.X99-lock

Xvfb :99 -screen 0 1440x900x24 -ac &
XVFB_PID=$!

export DISPLAY=:99

trap 'kill $XVFB_PID' EXIT INT TERM

exec python main.py