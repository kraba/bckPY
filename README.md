
# Backup PY

Il seguente script effettua :

a) backup di una o piu' directory contenenti qualsiasi tipo di file - parametro backup
b) dump del database mysql - parametro sql
c) rsync con altri server - parametro rsync
d) svecchiamento delle directory di backup - parametro clean
e) tutti i precedenti parametri in successione - parametro all

## Features

Per utilizzarlo e' necessario configurare il file di appoggio CONFIG, inserendo i campi necessari:

[var]
backuppath -> PATH DOVE EFFETTUARE IL BACKUP
logfile -> PATH E FILE DOVE E' PRESENTE IL FILE DI LOG GENERALE
logrsync -> PATH E FILE DOVE E' PRESENTE IL FILE DI LOG DI RSYNC
key -> PATH E FILE DOVE E' PRESENTE LA CHIAVE SSH

[mwpath]
path1 = /var/www/web -> PATH OGGETTO DI BACKUP

[rsync]
server1 = server,path,user -> INSERIRE IP, PATH E USER DEL SERVER DOVE FARE L'RSYNC

[clean]
clean1 = /var/bck,15 -> INSERIRE PATH E RETENTION PER BACKUP


Uso: ./mw-backup.py $foo $bar ...
