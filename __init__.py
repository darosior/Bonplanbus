# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash
import sqlite3
from time import strftime
from operator import itemgetter
import re
import os
import json


app = Flask(__name__)
#J'utilise ici une variable pour le nom et le chemin vers la base de donnée parceque sur le pi sinon la bdd se créait là
#où l'on lançait le script, avec cette varaiable ça la crée dans mon dossier.
#Modifier cette varriable en cas de changement de nom de dossier, chemin d'accès, ou encore de crontab
curdir = os.getcwd()
NomBdd=(curdir+'/database.db')

#Creation de la DB  (et connection) et de la table dedans.
conn = sqlite3.connect(NomBdd)
print 'Database opened.'
if conn.execute('CREATE TABLE IF NOT EXISTS bus_signales (num_ligne TEXT, nom_ligne TEXT, arret TEXT, heure TIME, comm TEXT, sens TEXT)'):
    print 'Table created or already created'
conn.close()

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
    
#trier la liste receptionnée
def trier_lignes(lignes):
    tmp=lignes
    lignes=[]    
    for i in tmp:
        if len(i)==1:
            lignes.append('A00'+i)
        if len(i)==2:
            lignes.append('A0'+i)
        if len(i)==3:
            lignes.append('A'+i)
    lignes=sorted(list(set(lignes)))
    tmp=lignes
    lignes=[]
    for i in tmp:
        i=re.sub(r'^A00', '', i)
        i=re.sub(r'^A0', '', i)
        i=re.sub(r'^A', '', i)
        lignes.append(i)
    return lignes
    
#Les fonctions qui suivent sont les fonctions qui renvoient les pages.
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/liste_bus')
def liste_bus():
    con = sqlite3.connect(NomBdd)
    con.row_factory = sqlite3.Row
    
    cur=con.cursor()
    cur.execute("SELECT heure, num_ligne, arret , comm from bus_signales")
    
    rows = cur.fetchall() #Pareil ici on met dans rows toutes les lignes récupérées avec select, on utilisera une boucle for
    #pour les recupérer
    commentaire = False #Pour passer aux templates pour gérer l'affichage en fonction de s'il y a un comm AFAIRE EN JS DEGEUU
    for row in rows:
        if row['comm']:
            commentaire = True
    return render_template('liste_bus.html',
                           rows=rows,
                           commentaire=commentaire)

@app.route('/signaler', methods=['POST', 'GET'])
def signaler():
    message=''
    err = False # Pour savoir quel style appliquer au message affiché    
    if request.method == 'POST':    
        try:
            con = sqlite3.connect(NomBdd)
            num_ligne=request.form['numero_ligne']
            nom_ligne=''
            arret=request.form['arret']
            comm=request.form['comm']
            sens=request.form['sens']
            heure=strftime('%H:%M:%S')
            if not test_signalement(comm):
                if arret=='' or num_ligne=='':
                    if comm != '':
                        info_lignes=ouvrir_lignes()
                        for ligne in info_lignes:
                            if ligne[0]==num_ligne and ligne[2]==sens:
                                nom_ligne=ligne[1]
                        cur = con.cursor()
                        cur.execute('INSERT INTO bus_signales (num_ligne, nom_ligne, arret, heure, comm, sens) VALUES (?, ?, ?, ?, ?, ?)', (num_ligne, nom_ligne, arret, heure, comm, sens))
                        con.commit()
                        message = u'Bus signalé, merci de votre contribution ! ' # Message que l'on va passer au template
                    else:
                        message = 'Merci de remplir le champs de commentaire si vous n\'indiquez pas l\'arret ou la ligne'
                        err = True
                else:
                    info_lignes=ouvrir_lignes()
                    for ligne in info_lignes:
                        if ligne[0]==num_ligne and ligne[2]==sens:
                            nom_ligne=ligne[1]
                    cur = con.cursor()
                    cur.execute('INSERT INTO bus_signales (num_ligne, nom_ligne, arret, heure, comm, sens) VALUES (?, ?, ?, ?, ?, ?)', (num_ligne, nom_ligne, arret, heure, comm, sens))
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
                           msg=message,
                           e=err)
  
@app.route('/a_propos')
def a_propos():
    return render_template('a_propos.html')

@app.route('/mentions')
def mentions():
    return render_template('mentions.html')
    
"""
Les fonctions pour les requêtes AJAX du JS
"""
#Récupérer le nom de la ligne en fonction du numero de ligne selectionné et de l'arrêt coché
@app.route('/nom_ligne', methods=['POST'])
def nom_ligne():
    if request.method=='POST':
        libelle=''
        sens=request.form['sens']
        num_ligne=request.form['numero_ligne']
        info_lignes=ouvrir_lignes()
        for ligne in info_lignes:
            if ligne[0]==num_ligne and ligne[2]==sens:
                libelle=ligne[1] #Comme ça il n'y aura toujours qu'un seul résultat à retourner au JS
        return libelle
    
#Récupérer les arrêts en fonction de la ligne choisie
@app.route('/afficher_arrets', methods=['POST'])
def afficher_arrets():
    if request.method=='POST':
        sens=request.form['sens']
        num_ligne=request.form['numero_ligne']
        try:
            con=sqlite3.connect(NomBdd)
            cur=con.cursor()
            cur.execute('SELECT arret FROM json_arrets WHERE desserte=? and sens =?;', (num_ligne, sens))
            arrets=sorted(list(set(cur.fetchall())))
        except Exception as e:
            print e.message, e.args
            con.rollback()
        con.close()
    return json.dumps(arrets)

#Récupérer les lignes
@app.route('/afficher_lignes', methods=['POST'])
def afficher_lignes():
    if request.method=='POST':
        try:
            con=sqlite3.connect(NomBdd)
            cur=con.cursor()
            cur.execute('SELECT desserte FROM json_arrets')
            lignes=cur.fetchall()
            tmp=lignes
            lignes=[]
            for i in tmp:
                i = i[0]
                lignes.append(i)
            lignes=trier_lignes(lignes)
            
        except Exception as e:
            con.rollback()
            print e.message, e.args
        con.close()
    return json.dumps(lignes)

@app.route('/recup_liste', methods=['POST'])
def recup_liste():
    if request.method=='POST':
        try:
            con = sqlite3.connect(NomBdd)
            con.row_factory = sqlite3.Row
            cur=con.cursor()
            cur.execute("SELECT heure, num_ligne, nom_ligne, arret , comm FROM bus_signales")
            rows = cur.fetchall()
            tmp=rows
            rows=[]
            for i in tmp:
                i=list(i)
                i[2]=i[1]+' '+i[2]
                i.remove(i[1])
                rows.append(i)
            print rows
        except Exception as e:
            print e.message, e.args
            con.rollback()
        con.close()
    return json.dumps(rows)
    
#Condition importante, si script éxécuté comme script principal ( pas importé )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80')
