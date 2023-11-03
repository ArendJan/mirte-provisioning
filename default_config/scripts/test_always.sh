#!/bin/bash

function do_for_sigint() {
 echo "sigint!"
 date > /home/mirte/stop.txt
 exit
}

trap 'do_for_sigint' 2
date > /home/mirte/test.txt
sleep infinity &
wait