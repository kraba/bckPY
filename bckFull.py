#!/usr/bin/python
# bckFull.py - Effettua backup di sistemi Unix
# Autore : Matteo Basso
# Versione : 0.1 - 16/12/2013
# Per ogni info : README.txt

import time
import sys
import os
import tarfile
import ConfigParser
import subprocess
import datetime
import paramiko 

#Funzione lettura file CONFIG
def popolaDict(file,section):
 dictConfig = {}
 fileConfig = ConfigParser.ConfigParser()
 fileConfig.read(file)
 options = fileConfig.options(section)
 for option in options:
        try:
                dictConfig[option] = fileConfig.get(section,option)
        except Exception,e:
                print("%s |EE| Errore in fase di popolamento var [%s] : %s" % (time.strftime("%d/%m/%Y %H:%M:%S"),section,str(e)))
                sys.exit()
 return dictConfig


#Funzione per apertura log file
def logOpen(logFile,comand):
 try:
    log = open(logFile,'aw')
    log.write("%s\n" % (50*"-"))
    log.write("%s |II| Inizio operazioni di backup \n" % time.strftime("%d/%m/%Y %H:%M:%S"))
    log.write("%s |II| Comando: %s \n" % (time.strftime("%d/%m/%Y %H:%M:%S"), comand))
    #print log
    return (log)
 except Exception,e:
	print("%s" % str(e))

# Funzione per chiusura log file
def logClose(log):
 try:
	log.write("%s |II| Fine operazioni di backup \n" % time.strftime("%d/%m/%Y %H:%M:%S"))
	log.close()
	return log
 except Exception,e:
        print("%s" % str(e))

#Funzione di creazione dei file *.tar.gz
def makeTar(dictConf,dictVar,log):
 for keyConfig,pathConfig in dictConf.items():
   # Controlla se il path esiste e se c'e' spazio libero > di 500 MB
   # o segnala errore   
   if os.path.exists(pathConfig) and freeSpace(dictVar['backuppath'],log):
     archiveFile = (keyConfig.upper() + '_BackupFile_' + (datetime.date.today()-datetime.timedelta(1)).strftime('%Y%m%d') + '.tar.gz')
     destinationPath = dictVar['backuppath']
     # Se e' presente uno / a fine path lo toglie (verra' aggiunto poi)
     if destinationPath.endswith('/'): destinationPath = destinationPath[:-1]
     # Compone il nome file
     output_filename = destinationPath + '/'  + archiveFile
     # Lancia il tar 
     if not os.path.exists(output_filename):
       with tarfile.open(output_filename, "w:gz") as tar:
         try:
     	    log.write("%s |II| Inizio creazione file %s \n" % (time.strftime("%d/%m/%Y %H:%M:%S"), output_filename))
     	    tar.add(pathConfig,arcname=os.path.basename(output_filename))
     	    log.write("%s |II| Fine creazione file %s \n" % (time.strftime("%d/%m/%Y %H:%M:%S"), output_filename))
    	 except Exception,e:
            log.write("%s |EE| Errore in fase di creazione %s con errore: %s \n" % (time.strftime("%d/%m/%Y %H:%M:%S"), output_filename, str(e)))
     else:
       log.write("%s |II| Il file %s e' gia' presente\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), output_filename))
   else:
     log.write("%s |EE| Controllare l'esistenza del path %s!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), pathConfig))
  
#Funzione di controllo spazio disco
def freeSpace(backupPath,log):
  du = os.statvfs(backupPath)
  # Calcolo in MB
  free = (du.f_bavail * du.f_frsize)/1048576
  # Se MB disponibili < 500 non effettua backup,avverte ed esce
  if (free < 500):
        log.write("%s |EE| Spazio disco < 500MB: %s MB - Backup non iniziato\n" % (time.strftime("%d/%m/%Y %H:%M:%S"),free))
	return False
  else: return True
	
#Funzione di lancio della procedura di rsync
def rSync(dictRsync,dictVar,log):
 # Apertura log rsync
 logRsync = open(dictVar['logrsync'],'aw')
 for keyRsync,infoRsync in dictRsync.items(): 
   # array contenente i valori del server 
   arrayInfoRsync = dictRsync[keyRsync].split(',')
   # Test ping : se il ping da risultato positivo si continua
   #Apertura devnull in scrittura
   devnull = open('/dev/null', 'w')
   replyPing = subprocess.call(['/usr/bin/fping',arrayInfoRsync[0]], stdout=devnull, stderr=subprocess.STDOUT)

   # Composizione del comando di rsync
   #cmdRsync = ('/usr/bin/rsync -agloptrv -e \"ssh -i ' + dictVar['key'] + '" ' + dictVar['backuppath'] + '/* ' + arrayInfoRsync[2] + '@' + \
   #             arrayInfoRsync[0] + ':' + arrayInfoRsync[1]) 
    
   # Composizione comando di unison
   # unison /backup/backup-wiki ssh://hb@panda//home/hb/bck-wiki -auto
   cmdRsync = ( '/usr/bin/unison ' + dictVar['backuppath'] + ' ssh://' + arrayInfoRsync[2] + '@' + arrayInfoRsync[0] + '/' +  arrayInfoRsync[1] + \
                ' -auto -silent')
   if replyPing == 0:
     log.write("%s |II| Inizio rsync su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoRsync[0]))
     subprocess.check_call([cmdRsync], shell=True, stdout=logRsync, stderr=subprocess.STDOUT)
     log.write("%s |II| Fine rsync su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoRsync[0]))
   else:
     log.write("%s |EE| il sistema %s non risponde al ping - rsync non eseguito!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoRsync[0]))
 logRsync.close()
 devnull.close()

#Funzione di pulizia - svecchiamento
def cleanDir(dictClean,log):
 devnull = open('/dev/null', 'w')
 for keyClean,infoClean in dictClean.items():
   # array contenente i valori del server 
   arrayInfoClean = dictClean[keyClean].split(',')
   # composizione comando di clean
   cmdClean = ('/usr/bin/find ' + arrayInfoClean[0] + ' -name \"*gz\" -mtime +' + arrayInfoClean[1] + ' -exec rm -f {} \;')
   # Controlla se il path esiste 
   if os.path.exists(arrayInfoClean[0]):
     log.write("%s |II| Inizio clean sul path %s - ritenzione %s giorni\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoClean[0], arrayInfoClean[1]))
     subprocess.check_call([cmdClean], shell=True, stdout=log, stderr=subprocess.STDOUT)
     log.write("%s |II| Fine clean sul path %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoClean[0]))
   else : 
     log.write("%s |EE| Controllare l'esistenza del path %s!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoClean[0]))
 devnull.close()


# Funzione di dump sql
#/usr/bin/mysqldump $DB_OPT1 -c | /bin/gzip -9 > $PATH_BCK/DBFullDUMP.$(date '+%Y%m%d').sql.gz || exit $?
#wiki -u wikidb --password=wikidb"
def sqlDump(dictSql,dictVar,log):
 logSql = open(dictVar['logsql'],'aw')
 for keySql,infoSql in dictSql.items():
   arrayInfoSql = dictSql[keySql].split(',')
   # Se array dei dati < 5 elementi non fa nulla - mancano dati
   if len(arrayInfoSql) != 6: 
      log.write("%s |EE| Nella sezione [sql] per %s mancano dei paramentri!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), keySql.upper()))
      pass 
   arraySqlLocation = arrayInfoSql[0].split('|')
  
   # Se e' presente uno / a fine path lo toglie (verra' aggiunto poi)
   destinationPath = arrayInfoSql[5]
   if destinationPath.endswith('/'): destinationPath = destinationPath[:-1]
   # Compone il nome file con il path di destinazione
   sqlFile = (keySql.upper() + '_DBDump_' + (datetime.date.today()-datetime.timedelta(1)).strftime('%Y%m%d') + '.sql.gz')
   outputSql = destinationPath + '/'  + sqlFile

   # Se il DB e' remoto procede al dump
   if arraySqlLocation[0] == 'remote':
     # Test ping : se il ping da risultato positivo si continua
     #Apertura devnull in scrittura
     devnull = open('/dev/null', 'w')
     replyPing = subprocess.call(['/usr/bin/fping',arrayInfoSql[1]], stdout=devnull, stderr=subprocess.STDOUT)

     if replyPing == 0:
       log.write("%s |II| Inizio dump DB %s su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[4], arrayInfoSql[1] ))
       try:
         sshClient = paramiko.SSHClient()
         sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         sshClient.connect(arrayInfoSql[1], username=arraySqlLocation[1])
         def sshFunct(cmd):
             outer = []
             msg = [stdin, stdout, stderr] = sshClient.exec_command(cmd)
             for item in msg:
                try:
                   for line in item:
                      outer.append(line.strip('\n'))
                except: pass 
             return(outer)
         
         # Controlla se il path inserito in CONFIG esiste
         sftp = sshClient.open_sftp()
         sftp.chdir(arrayInfoSql[5])
         isPathCorrect = sftp.getcwd()
	 # Se il path esiste e non e' None va avanti, altrimenti lancia except	
         if isPathCorrect != None: 
           dump = sshFunct('/usr/bin/mysqldump ' + arrayInfoSql[4] + ' -u ' + arrayInfoSql[2] + ' --password=' + arrayInfoSql[3] + ' -c |/bin/gzip -9 > ' + outputSql) 
           log.write("%s |II| Fine dump DB %s su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[4], arrayInfoSql[1] ))
           log.write("%s |II| Il file non e' stato copiato in locale, effettuare sync\n" % (time.strftime("%d/%m/%Y %H:%M:%S")))

       except Exception,e:
            log.write("%s |EE| Errore in fase di creazione %s con errore: %s \n" % (time.strftime("%d/%m/%Y %H:%M:%S"), sqlFile, str(e)))
     else : 
       log.write("%s |EE| il sistema %s non risponde al ping - DB dump non eseguito!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[1]))

   # Se il DB e' locale procede al dump
   elif arraySqlLocation[0] == 'local' :
    if os.path.exists(arrayInfoSql[5]):
     log.write("%s |II| Inizio dump DB %s su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[4], arrayInfoSql[1] ))
     dumpSqlLocal = ('/usr/bin/mysqldump ' + arrayInfoSql[4] + ' -u ' + arrayInfoSql[2] + ' --password=' + arrayInfoSql[3] + ' -c |/bin/gzip -9 > ' + outputSql)
     subprocess.check_call([dumpSqlLocal], shell=True, stdout=logSql, stderr=subprocess.STDOUT)     
     log.write("%s |II| Fine dump DB %s su server %s\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[4], arrayInfoSql[1] ))
    else:
     log.write("%s |EE| Sql dump non eseguito - controllare l'esistenza del path %s!!!\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), arrayInfoSql[5]))
   
   # Se nel file CONFIG e' scritta porcheria segnala errore
   else:
     log.write("%s |EE| Controllare il file CONFIG per [sql], errori rilevati\n" % (time.strftime("%d/%m/%Y %H:%M:%S")))
 logSql.close()

############# MAIN ###################
def main(): 

 try:
  # Popolazione dict per sezione [var]
  dictVar = popolaDict("CONFIG", 'var')
  # Apertura log
  comand = sys.argv[0:]
  #if os.path.getsize(dictVar['logfile']) > '2097152':
  log = logOpen(dictVar['logfile'], comand)  
  # Popolazione dict per sezione [mwpath]
  dictConf = popolaDict("CONFIG", 'mwpath')
  # Popolazione dict per sezione [rsync]
  dictRsync = popolaDict("CONFIG", 'rsync')
  # Popolazione dict per sezione [clean]
  dictClean = popolaDict("CONFIG", 'clean') 
  # Popolazione dict per sezione [sql]
  dictSql = popolaDict("CONFIG", 'sql')

  if len(sys.argv) > 1:
   for value in sys.argv[1:]:
    if (value == 'tar'): 
        makeTar(dictConf,dictVar,log)
    elif (value == 'rsync'):
	rSync(dictRsync,dictVar,log)
    elif (value == 'sql'):
	sqlDump(dictSql,dictVar,log)    
    elif (value == 'clean'):
        cleanDir(dictClean,log)
    elif (value == 'all'):
	makeTar(dictConf,dictVar,log)
        sqlDump(dictSql,dictVar,log)
        cleanDir(dictClean,log)
        rSync(dictRsync,dictVar,log)
    elif (value == 'help'):
	fileHelp = open("README.txt", "r")
	text = fileHelp.read()
	print text
	fileHelp.close()	
    else :
	log.write("%s |EE| Il parametro %s non e' valido, help per i parametri validi\n" % (time.strftime("%d/%m/%Y %H:%M:%S"), value))
  else: print('Attenzione, lo script funziona solo con parametri. \nLeggere il file README.txt o lanciare lo script con parametro help!') 
  # Chiusura log
  log = logClose(log)  

 except Exception,e:
  print("%s |EE| Errore in fase di backup : %s" % ( time.strftime("%d/%m/%Y %H:%M:%S"), str(e) ))
  sys.exit()

########################################
if __name__ == "__main__":
 main()
