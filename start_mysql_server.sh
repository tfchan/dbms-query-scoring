#!/bin/sh
is_init_complete () {
    docker logs some-mysql 2>&1 | grep "port: 3306  MySQL Community Server"
}

docker run --name some-mysql -e MYSQL_ROOT_PASSWORD="dbms" -d mysql:5.7
if [ $? != 0 ]
then
    exit 1
fi
# Wait for init complete
is_init_complete
while [ $? != 0 ]
do
    sleep 1
    is_init_complete
done
exit 0
