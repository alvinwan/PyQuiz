#!/usr/bin/env bash

echo '1 check:'

exit=`python3 --version`
[ $? != 0 ] && echo '[Error] Python3 not found' || echo '[OK] Python3 found'
