#!/bin/sh

here="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $here
sed "s/user/${1}/g" ${here}/create_user_and_database.sql > tmp1.sql
sed "s/database/${2}/g" tmp1.sql > tmp2.sql
sed "s/password/${3}/g" tmp2.sql > tmp1.sql
psql postgres -f tmp1.sql
rm tmp1.sql
rm tmp2.sql
