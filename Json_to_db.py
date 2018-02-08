# -*- coding: utf-8 -*-

#Script python qui recupere le json et le stocke dans la base de donnees
#A repeter chaque semaine/jour avec cron

import json
import urllib
import sqlite3 as db
from operator import itemgetter
from time import strftime
import os
import unicodedata

curdir=os.getcwd()
NomBdd=(curdir+'/database.db')
data=[]
log=open(curdir+'/Database_log', 'at')

log.write('\n')
def recuperer_json(url):
    global log
    try:
        data = json.load(urllib.urlopen(url))['values']
        print('Fichier json telecharge')
        log.write('\n('+ strftime('%d/%m') +') Fichier json telecharge à ' + strftime('%H:%M:%S'))
    except IOError, e:
        print('Erreur lors du chargement du fichier json')
        log.write('\n('+ strftime('%d/%m') +') Erreur lors du chargement du fichier json à ' + strftime('%H:%M:%S'))
        log.write('\n'+e.reason+' à ' + strftime('%H:%M:%S'))
    return data

#nomtable est le nom de la table
def supprimer(nomtable):
    global log
    with db.connect(NomBdd) as con:
	    try:
              con.execute('DROP TABLE IF EXISTS ' + nomtable)
              con.commit()
              print('Table supprimee')
              log.write('\n ('+ strftime('%d/%m') +')  Table '+nomtable+' supprimee à ' + strftime('%H:%M:%S'))
	    except:
             con.rollback()
             print('Erreur lors suppression de la table')
             log.write('\n('+ strftime('%d/%m') +') Erreur lors de la suppression de la table '+nomtable+' à ' + strftime('%H:%M:%S'))
    con.close()

if __name__ == '__main__':
    #On recupere depuis la plateforme d'open data de tcl les json contenant les lignes et arrets.
    lignes_data = sorted(recuperer_json('https://download.data.grandlyon.com/ws/rdata/tcl_sytral.tcllignebus/all.json'), key=itemgetter('ligne'))
    arrets_all = recuperer_json('https://download.data.grandlyon.com/ws/rdata/tcl_sytral.tclarret/all.json')
    """
    #Pour stocker dans un fichier sous forme json pour le récupérer avec le javascript
    with open('arret_ligne', 'w') as arret_ligne:    
        arret_ligne.write('{"fields":["arret", "ligne"], "values":[')        
        for arret in arrets_all:
            if arret['nom'] and arret['desserte']:
                arret['nom']=unicodedata.normalize('NFKD',arret['nom']).encode('ascii', 'ignore')
                arret['desserte']=arret['desserte'].encode('ascii', 'ignore').decode('ascii')
                arret['nom']=arret['nom'].encode('ascii', 'ignore').decode('ascii')
                arret_ligne.write('{"arret":"' +arret['nom'] +'", "ligne":"'+arret['desserte']+ '"},')
        arret_ligne.write(']}')
    arret_ligne.close()
    """
    #On supprime la table, puisque c'est une MAJ.    
    supprimer('json_ligne')
    supprimer('json_arrets')
    
    #On se connecte a la DB.
    con = db.connect(NomBdd)
    try:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS json_ligne (ligne CHAR(10), libelle CHAR(100), sens CHAR(10));')
        #Puisque ce sera un script pour des mises a jour, on verifie si la table existe, sinon on la cree.
        #Ceci est une boucle for pour stocker le meme nombre de caractere pour chasue ligne (4) dans la base de donnee.
        #Sinon le tri n'est pas effectif sur la page signaler.html dans les formulaires. 
        #Cf la boucle for pour les supprimer dans le fichier __init__.py
        for ligne_actuelle in lignes_data:
            if len(ligne_actuelle['ligne']) == 1:
                ligne_actuelle['ligne']='000'+ligne_actuelle['ligne']
            elif len(ligne_actuelle['ligne'])== 2:
                ligne_actuelle['ligne']='00'+ligne_actuelle['ligne']
            elif len(ligne_actuelle['ligne'])== 3:
                ligne_actuelle['ligne']='0'+ligne_actuelle['ligne']
            cur.execute('INSERT INTO json_ligne (ligne, libelle, sens) VALUES (:ligne, :libelle, :sens);', (ligne_actuelle))
            #On stock les donnees du dictionnaire, le ":" dans les arguments de VALUES est une propriete SQL pour les dictionnaires
            #qui permet un code plus concis.
         
        #Dans cette boucle on stocke dans la base les arrets en fonction de leurs dessertes et on affiche en plus leur sens, cf bouton radio page signaler
        cur.execute('CREATE TABLE IF NOT EXISTS json_arrets (desserte CHAR(10), arret CHAR(64), sens CHAR(10));')    
        for arret_actuel in arrets_all:
            dessertes=[]
            dessertes=arret_actuel['desserte'].split(',')
            for desserte in dessertes:
                if ':A' in desserte:
                    desserte=desserte.split(':')[0]
                    if 'A' in desserte:
                        desserte=desserte.replace('A','')
                    if 'B' in desserte:
                        desserte=desserte.replace('B','')
                    cur.execute('INSERT INTO json_arrets (desserte, arret, sens) VALUES (?, ?, ?);', (desserte, arret_actuel['nom'], 'Aller'))
                if ':R' in desserte:
                    desserte=desserte.split(':')[0]
                    if 'A' in desserte:
                        desserte=desserte.replace('A','')
                    if 'B' in desserte:
                        desserte=desserte.replace('B','')
                    cur.execute('INSERT INTO json_arrets (desserte, arret, sens) VALUES (?, ?, ?);', (desserte, arret_actuel['nom'], 'Retour'))

        print('MAJ OK')
        log.write('\n('+ strftime('%d/%m') +') MAJ OK à ' + strftime('%H:%M:%S'))

    except db.Error as e:
        print e.message
        log.write('\n'+ e.message+' à ' + strftime('%H:%M:%S'))
        con.rollback()
        print('Erreur lors du stockage dans la base de donnees')
        log.write('\n('+ strftime('%d/%m') +') Erreur lors du stockage dans la base de donnees à ' + strftime('%H:%M:%S'))
        #Si ca foire on affiche un message et on recharge a la derniere sauvegarde. 
    con.commit()
    con.close()
    #On sauvegarde et on ferme la DB

    print('DONE')
    