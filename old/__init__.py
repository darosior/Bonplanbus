# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash
import sqlite3
from time import strftime
from operator import itemgetter
import re
import os


app = Flask(__name__)
#J'utilise ici une variable pour le nom et le chemin vers la base de donnée parceque sur le pi sinon la bdd se créait là
#où l'on lançait le script, avec cette varaiable ça la crée dans mon dossier.
#Modifier cette varriable en cas de changement de nom de dossier, chemin d'accès, ou encore de crontab
curdir = os.getcwd()
NomBdd=(curdir+'/database.db')

#Creation de la DB  (et connection) et de la table dedans.
conn = sqlite3.connect(NomBdd)
print 'Database opened.'
if conn.execute('CREATE TABLE IF NOT EXISTS bus_signales (infos TEXT, arret TEXT, heure TIME, comm TEXT)'):
    print 'Table created or already created'
conn.close()


#Des variables globales pour les boucles jinja dans le template "signaler".
ligne_actuelle=0
arret_actuel=0
i=0
#Les deux fonctions qui suivent sont declarees afin de rendre le code plus clair et de ne pas
#surcharger la fonction qui renvoit la page de signalement
def ouvrir_lignes():
    try:
        con = sqlite3.connect(NomBdd) #On se connecte a la bdd 
        cur = con.cursor()
        cur.execute('SELECT ligne, libelle, sens FROM json_ligne ORDER BY ligne') #On recupere toutes les infos des lignes
        lignes_data = cur.fetchall() #On selectionne toutes les lignes récupérées avec select
        lignes_data = sorted(list(set(lignes_data)), key=itemgetter(0)) #tri
        tmp=lignes_data # On va travailler sur une liste temporaire,
        lignes_data=[] #On vide la liste qui nous interesse
        #On va a present dans cette boucle for supprimer les zeros, maintenant que notre tri est realise.
        #On utilise le module 're'
        for ligne in tmp:
            ligne=list(ligne)#Les tuples ne sont pas modifiiables
            ligne[0]=re.sub(r'^000', '', ligne[0])
            ligne[0]=re.sub(r'^00', '', ligne[0])
            ligne[0]=re.sub(r'^0', '', ligne[0])
            lignes_data.append(ligne)#On recree la liste qui nous interesse de facon modifiee  
        con.close()
    except:
        print('Erreur lors de la connection a la base de donnees, pour recuperer les lignes.')
    return lignes_data

def ouvrir_arrets():
    try:
        con = sqlite3.connect(NomBdd)
        cur = con.cursor()
        cur.execute('SELECT arret FROM json_arrets')
        arrets_data = sorted(list(set(cur.fetchall())))
    except:
        print('Erreur lors de la connection a la base de donnees, pour recuperer les arrets.')
                
    return arrets_data
    
def ouvrir_arret_ligne():
    try:
        with open('arret_ligne', 'r') as al:
            arret_ligne=al.read()
        al.close()
    except:
        print('Erreur lors de la lecture du fichier arret_ligne.')
    return arret_ligne
    
#Fonction qui va faire les tests de validité des signalements
#Ne prend (pour l'instant) en argument que le commentaire laissé par l'utilisateur. A terme il verifiera les arrets en fonction
#des lignes
def test_signalement(commentaire):
    invalide = False
    with open('insultes', 'r') as insultes:
        for insulte in insultes:
            insulte = unicode(insulte, 'utf-8') #Sinon erreur d'encodage
            if commentaire:
                if insulte.lower() in commentaire.lower():
                    invalide = True
        if invalide:
            return True
        else:
            return False
    insultes.close()
    
#Les fonctions qui suivent sont les fonctions qui renvoient les pages.
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/liste_bus')
def liste_bus():
    con = sqlite3.connect(NomBdd)
    con.row_factory = sqlite3.Row
    
    cur=con.cursor()
    cur.execute("SELECT heure, infos, arret , comm from bus_signales")
    
    rows = cur.fetchall() #Pareil ici on met dans rows toutes les lignes récupérées avec select, on utilisera une boucle for
    #pour les recupérer
    commentaire = False #Pour passer aux templates pour gérer l'affichage en fonction de s'il y a un comm
    for row in rows:
        if row['comm']:
            commentaire = True
    return render_template('liste_bus.html',
                           rows=rows,
                           commentaire=commentaire)

@app.route('/signaler', methods=['POST', 'GET'])
def signaler():
    global ligne_actuelle, arret_actuel, heures
    #On appelle les fonctions definies plus haut et on stocke ce qu'elles
    #retournent dans une variable que l'on va passer au template.
    lignes_data=ouvrir_lignes()
    arrets_data=ouvrir_arrets()
    arret_ligne = ouvrir_arret_ligne()#les arrets en fonction des lignes, je ne l'utilise pas ppour l'instant mais je vais sûrement utiliser de l'AJAX pour ça
    arret_ligne=arret_ligne.replace('},]}', '}]}')
    print arret_ligne
    message=''
    err = False # Pour savoir quel style appliquer au message affiché    
    if request.method == 'POST':
        con = sqlite3.connect(NomBdd)    
        try:
            infos=request.form['infos']#Rien a dire pour cette fonction de special, on utilise request pour 'dialoguer' ou du moins
            arret=request.form['arret']
            comm=request.form['comm']
            heure=strftime('%H:%M:%S')
            if not test_signalement(comm):
                if arret=='' or infos=='':
                    if comm != '':
                        cur = con.cursor()
                        cur.execute('INSERT INTO bus_signales (infos, arret, heure, comm) VALUES (?, ?, ?, ?)', (infos, arret, heure, comm))
                        con.commit()
                        message = u'Bus signalé, merci de votre contribution ! ' # Message que l'on va passer au template
                    else:
                        message = 'Merci de remplir le champs de commentaire si vous n\'indiquez pas l\'arret ou la ligne'
                        err = True
                else:
                    cur = con.cursor()
                    cur.execute('INSERT INTO bus_signales (infos, arret, heure, comm) VALUES (?, ?, ?, ?)', (infos, arret, heure, comm))
                    con.commit()
                    message = u'Bus signalé, merci de votre contribution !'# Message que l'on va passer au template
            else:
                message = u'Merci de remplir le champs de commentaire avec des informations valides (pas d\'insultes, etc..)'
                err = True
        except Exception as e:
            con.rollback()
            print e.message, e.args
            message = u'Erreur lors du signalement du bus. Assurez-vous d\'avoir suivi les instructions et d\'avoir bien rempli TOUS les champs de la BONNE facon (le bon sens et le bon arret correspondant a la bonne ligne, un peu de bon sens!)'
            err = True
        
        con.close()
    return render_template('signaler.html', 
                           lignes_data=lignes_data,
                           arrets_data=arrets_data,
                           arret_ligne=arret_ligne,
                           msg=message,
                           e=err)
    
@app.route('/a_propos')
def a_propos():
    return render_template('a_propos.html')

@app.route('/mentions')
def mentions():
    return render_template('mentions.html')

#Condition importante, si script éxécuté comme script principal ( pas importé )
if __name__ == '__main__':
    app.run(debug=True)
