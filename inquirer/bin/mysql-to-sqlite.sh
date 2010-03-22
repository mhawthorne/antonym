#!/bin/sh

alias sed=gsed

grep -v ' KEY "' < /dev/stdin |
grep -v ' UNIQUE KEY "' |
grep -v ' PRIMARY KEY ' |
sed 's/ unsigned / /g' |
sed 's/ auto_increment/ primary key autoincrement/gi' |
sed 's/ smallint([0-9]*) / integer /gi' |
sed 's/ tinyint([0-9]*) / integer /gi' |
sed 's/ int([0-9]*) / integer /gi' |
sed 's/ character set [^ ]* / /gi' |
sed 's/ enum([^)]*) / varchar(255) /gi' |
sed 's/ on update [^,]*//gi' |
perl -e 'local $/;$_=<>;s/,\n\)/\n\)/gs;print "begin;\n";print;print "commit;\n"' |
perl -pe '
if (/^(INSERT.+?)\(/) {
 $a=$1;
 s/\\'\''/'\'\''/g;
 s/\\n/\n/g;
 s/\),\(/\);\n$a\(/g;
}
'