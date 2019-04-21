#!/bin/sh
docker run --name some-mysql -e MYSQL_ROOT_PASSWORD="dbms" -d mysql:5.7
if [ $? != 0 ]
then
    exit 1
fi
complete_str="ready for connections"
# Wait for init complete
docker logs some-mysql 2>&1 | grep "ready for connections"
while [ $? != 0 ]
do
    sleep 1
    docker logs some-mysql 2>&1 | grep "ready for connections"
done
exit 0
