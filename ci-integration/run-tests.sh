#!/bin/sh

export CI=travis
export FAST_FAIL=1


# The context should already have been activated at this point.
#pip install pymongo pytest pytest-bdd pytest-cov
#pip install mock --upgrade
#pip install pytest pytest-timeout --upgrade

pip list
exit_code=0

# Break up the tests to work around the issue in #754. Breaking them up allows 
# the files to be closed with the individual pytest processes
echo "Current Environment of Execution"
ls -la
echo "PATH"
echo "$PATH"
echo "PYTHONPATH"
echo "$PYTHONPATH"
echo "VOLTTRON is at"
which volttron
which volttron-ctl
echo "python is at"
which python

#directories that need split into individual files
filedirs="volttrontesting/platform"
#directories that can be called as normal (recursive)
testdirs="services/core/VolttronCentral/tests services/core/VolttronCentralPlatform/tests examples volttron volttrontesting/gevent volttrontesting/multiplatform volttrontesting/subsystems volttrontesting/testutils volttrontesting/zmq"
#directories that must have their subdirectories split
splitdirs="services/core/* services/contrib/*"

echo "installing ERLANG"
wget -O - 'https://dl.bintray.com/rabbitmq/Keys/rabbitmq-release-signing-key.asc' | sudo apt-key add -
echo 'deb https://dl.bintray.com/rabbitmq/debian trusty erlang-21.x'|sudo tee --append /etc/apt/sources.list.d/bintray.erlang.list
sudo apt-get update
sudo apt-get purge erlang*
sudo apt-get install -yf
sudo apt-get install -y erlang-diameter erlang-eldap
sudo apt-get install -y erlang-nox

echo "bootstrapping RABBITMQ"
python bootstrap.py --rabbitmq --market

echo "rabbitmq status"
"$HOME/rabbitmq_server/rabbitmq_server-3.9.29/sbin/rabbitmqctl" status

echo "TestDirs"
for dir in $testdirs; do
  echo "*********TESTDIR: $dir"
  pytest -s -v "$dir"

  tmp_code=$?
  exit_code=$tmp_code
  echo $exit_code
  if [ $tmp_code -ne 0 ]; then
    if [ $tmp_code -ne 5 ]; then
      if [ ${FAST_FAIL} ]; then
        echo "Fast failing!"
        exit $tmp_code
      fi
    fi
  fi
done

echo "SplitDirs"
for dir in $splitdirs; do

    for D in $dir; do
        for p in $testdirs; do
            if [ "$p" = "$D" ]; then
                echo "ALREADY TESTED DIR: $p";
                continue;
            fi;
        done

        if [ -d "${D}" ]; then
            echo "*********SPLITDIR: $D"
            pytest -s -v "${D}"
            tmp_code=$?
            if [ $tmp_code -ne 0 ]; then
              if [ $tmp_code -ne 5 ]; then
                if [ ${FAST_FAIL} ]; then
                  echo "Fast failing!"
                  exit $tmp_code
                fi
                exit_code=$tmp_code
              fi
            fi
        fi
    done
done

echo "File tests"
for dir in $filedirs; do
  echo "File test for dir: $dir"
  for testfile in "$dir"/*.py; do
    echo "Using testfile: $testfile"
    if [ "$testfile" != "volttrontesting/platform/packaging-tests.py" ]; then
       pytest -s -v "$testfile"

       tmp_code=$?
       exit_code=$tmp_code
       echo "$exit_code"
       if [ $tmp_code -ne 0 ]; then
         if [ $tmp_code -ne 5 ]; then
           if [ ${FAST_FAIL} ]; then
             echo "Fast failing!"
             exit $tmp_code
           fi
         fi
       fi
       else
         echo "Skipping $testfile"
     fi
   done
done

exit $exit_code
