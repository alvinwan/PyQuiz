#!/usr/bin/env bash

# install virtualenv
check=`virtualenv --version`
[ $? != 0 ] && sudo pip3 install virtualenv

# check for virtualenv
python3 -m venv env

# activate virtualenv
source env/bin/activate

# install
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "[OK] Installation complete.
You are now in the virtualenv. Note the (env) prefix before your command prompt:
- To exit, CTRL+C or 'deactivate'.
- To re-enter the virtual environment, 'source activate.sh'."
