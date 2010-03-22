#!/bin/sh

if [ $# -ne 1 ]; then
    echo "ERROR - expected <where-clause>"
    exit 1
fi

where=$1

sqlite3 -csv data/milhouse.db "select id, nick||'/milhouse', message, date from messages where $where order by date"