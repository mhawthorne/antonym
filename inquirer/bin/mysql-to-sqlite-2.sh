#!/bin/sh -e

alias sed=gsed

grep -v " KEY \`" - |
grep -v " UNIQUE KEY \`" |
grep -v ' PRIMARY KEY ' |
sed 's/^SET.*;//g' |
sed 's/ UNSIGNED / /g' |
sed 's/ auto_increment/ primary key autoincrement/g' |
sed 's/ smallint([0-9]*) / integer /g' |
sed 's/ tinyint([0-9]*) / integer /g' |
sed 's/ int([0-9]*) / integer /g' |
sed 's/ enum([^)]*) / varchar(255) /g' |
sed 's/ on update [^,]*//g' |
sed "s/\\\'/''/g" |                                                                                    # convert MySQL escaped apostrophes to SQLite   \' =&gt; ''
sed 's/\\\"/"/g' |                                                                                    # convert escaped double quotes into regular quotes
sed 's/\\\n/\n/g' |
sed 's/\\r//g' |
perl -e 'local $/;$_=<>;;s/,\n\)/\n\)/gs;print "begin;\n";print;print "commit;\n"' |
perl -pe '
if (/^(INSERT.+?)\(/) {
  $a=$1;
  s/\\'\''/'\'\''/g;
  s/\\n/\n/g;
  s/\),\(/\);\n$a\(/g;
}
'