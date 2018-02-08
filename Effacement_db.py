# -*- coding: utf-8 -*-

#Ce mini-script est un script qui supprime la table des bus signales dans la DB.
#Il sera planifie avec cron/crontab pour s'executer tous les jours a 3:00 du matin, ATTENTION pour eviter des erreurs, bien relancer __init__.py apres la modification
#Il ecrit dans le fichier database.log

import sqlite3 as db
from time import strftime
import os

curdir=os.getcwd()
NomBdd=(curdir+'/database.db')

with db.connect(NomBdd) as con:
    log=open(curdir+'/Database_log', 'at')
    log.write('\n')
    try:
        print 'Database opened'
        log.write('\n('+ strftime('%d/%m') +') Database opened at ' + strftime('%H:%M:%S'))
        con.execute('DROP TABLE IF EXISTS bus_signales')
        print 'Table bus_signales was removed from the database'
        log.write('\n('+ strftime('%d/%m') +') Table bus_signales was removed from the database at ' + strftime('%H:%M:%S'))
        log.write('\n')
    except:
        con.rollback()
        print 'An error occured when removing table from database'
        log.write('\n('+ strftime('%d/%m') +') An error occured when removing table from database at ' + strftime('%H:%M:%S'))

con.commit()
con.close()
log.close()

