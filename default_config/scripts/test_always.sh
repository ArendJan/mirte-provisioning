#!/bin/bash

function do_for_sigint() {
 echo "sigint!"
 exit
}

trap 'do_for_sigint' 2
date > /home/mirte/test.txt