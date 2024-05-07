#installation librairie
import os
import pickle
import pandas as pd
import pdfplumber
from prophet import Prophet
import calendar
import pyodbc
from flask import Flask, jsonify, render_template, request,  redirect, sessions, url_for, flash, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

# from flask_bcrypt import Bcrypt
from functools import wraps
from werkzeug.utils import secure_filename
# from flask_sse import sse
# import json
# from flask_socketio import SocketIO, emit, join_room

# from flask_login import current_user, login_required
app = Flask(__name__)
# bcrypt = Bcrypt(app)
# socketio = SocketIO(app)

#connexion à la base de données
conn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                      "Server=DESKTOP-AE2L96K\SQLEXPRESS;"
                       "Database=spm;"
                       "Trusted_Connection=yes")

#fonction de restriction à l'app si l'user n'est pas connecté
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # L'utilisateur n'est pas connecté, rediriger vers la page de connexion
            flash("Vous n'êtes pas autorisé à effectuer cette action", "warning")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

#index
@app.route("/")
def index():
    return render_template("authentification/login.html")

#inscription
@app.route("/inscription")
def inscription():
    return render_template("authentification/register.html")

@app.route('/traitement_inscription', methods=['POST'])
def traitement():
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    role = request.form['role']

#verification valeur role 
    if role =="#":
        flash("Veuillez entrer un rôle valide","danger")
        return redirect(url_for('inscription'))

# Vérification de l'existence de l'utilisateur par email
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE Email = ?", (email,))
    user_exists = cursor.fetchone()[0]

    if user_exists:
        flash("L'utilisateur avec l'adresse email " + email + " existe déjà.","danger")
        return redirect(url_for('inscription'))
    
# Insertion dans la table users
    cursor.execute("INSERT INTO users (Email, Roles) VALUES (?, ?)", (email, role))
    conn.commit()

# Récupération de l'ID de l'utilisateur inscrit
    cursor.execute("SELECT @@IDENTITY AS 'ID'")
    user_id = cursor.fetchone()[0]

# Insertion dans la table correspondante selon le rôle
    if role == "Admin":
        cursor.execute("INSERT INTO Admin (IdUser, NomAdmin, PrenomAdmin) VALUES (?, ?, ?)", (user_id, nom, prenom))
    elif role == "Gestionnaire":
        cursor.execute("INSERT INTO Gestionnaire (IdUser, NomGestionnaire, PrenomGestionnaire) VALUES (?, ?, ?)", (user_id, nom, prenom))
    elif role == "Vendeur":
        cursor.execute("INSERT INTO Vendeur (IdUser, NomVendeur, PrenomVendeur) VALUES (?, ?, ?)", (user_id, nom, prenom))
    else:
        raise ValueError("Rôle invalide")

    conn.commit()
    cursor.close()

    flash("Félicitation ! accès autoriser à " + email ,"success")
    return redirect(url_for('inscription'))


#confirmez acces
@app.route("/confirmez_acces")
def confirmez_acces():
    return render_template("authentification/confirmez_acces.html")

@app.route("/traitement_confirmation_acces", methods=['POST'])
def traitement_confirmation_acces():
    email = request.form['email']
    mdp = request.form['mdp']
    confirme_mdp = request.form['confirme_mdp']

    # Vérifier si les mots de passe correspondent
    if mdp != confirme_mdp:
        flash("Les mots de passe ne correspondent pas", "danger")
        return redirect(url_for('confirmez_acces'))

    # Hasher le mot de passe
    mot_de_passe_hash = generate_password_hash(mdp)

    # Vérification de l'existence de l'utilisateur par email
    cursor = conn.cursor()
    cursor.execute("SELECT IdUser, mot_de_passe FROM users WHERE Email = ?", (email,))
    result = cursor.fetchone()

    if result:
        user_id, existing_password = result
        if existing_password is None:
            cursor.execute("UPDATE users SET mot_de_passe = ? WHERE IdUser = ?", (mot_de_passe_hash, user_id))
            conn.commit()  
            flash("Félicitations ! Vous avez terminé votre inscription.", "success")
            return redirect(url_for('index'))
        else:
            flash("Vous n'êtes pas autorisé à effectuer cette action", "danger")
            return redirect(url_for('index'))
    else:
        flash("Vous n'êtes pas autorisé à accéder à cette page", "danger")
        return redirect(url_for('confirmez_acces'))
    

# Route de connexion
@app.route("/connexion", methods=['POST'])
def connexion():
    email = request.form['email']
    mdp = request.form['mdp']

    # Vérification de l'existence de l'utilisateur par email
    cursor = conn.cursor()
    cursor.execute("SELECT IdUser, mot_de_passe, Roles FROM users WHERE Email = ?", (email,))
    result = cursor.fetchone()

    if result:
        user_id, hashed_password, role = result
        if hashed_password is None:
            flash("Vous devez terminer votre inscription en confirmant votre mot de passe.", "warning")
            return redirect(url_for('confirmez_acces'))
        # Vérifier si le mot de passe est correct en utilisant check_password_hash
        elif check_password_hash(hashed_password, mdp):
            # Enregistrement de l'ID de l'utilisateur dans la session
            session['user_id'] = user_id
            # Authentification réussie, rediriger vers une page en fonction du rôle de l'utilisateur
            if role == "Admin":
                flash("Connexion réussie en tant qu'administrateur !", "success")
                return redirect(url_for('dash'))
            elif role == "Gestionnaire":
                flash("Connexion réussie en tant que gestionnaire !", "success")
                return redirect(url_for('dash_gestionnaire'))
            elif role == "Vendeur":
                flash("Connexion réussie en tant que vendeur !", "success")
                return redirect(url_for('dash_vendeur'))
            else:
                flash("Rôle non reconnu.", "danger")
                return redirect(url_for('index'))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            return redirect(url_for('index'))
    else:
        flash("Email ou mot de passe incorrect.", "danger")
        return redirect(url_for('index'))

#deconnexion
@app.route("/deconnexion")
def deconnexion():
    session.pop('user_id', None)  # Supprimer l'ID de l'utilisateur de la session
    flash("Félicitation, vous êtes déconnecté.e !", "success")
    return redirect(url_for('index'))



##########Dashbord_admin############
@app.route("/dash")
@login_required
def dash():
    user_id = session.get('user_id')
    cursor = conn.cursor()

    # Requête pour obtenir les informations de l'admin
    cursor.execute("SELECT * FROM Admin WHERE IdUser = ?", (user_id,))
    data = cursor.fetchall()

    # Requête pour compter le nombre de gestionnaires
    cursor.execute("SELECT COUNT(*) FROM Gestionnaire")
    gestionnaire_count = cursor.fetchone()[0]

    # Requête pour compter le nombre de vendeurs
    cursor.execute("SELECT COUNT(*) FROM Vendeur")
    vendeur_count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()

    return render_template("admin/dash.html", user_id=user_id, data=data, gestionnaire_count=gestionnaire_count, vendeur_count=vendeur_count)



#Deployement_model#
# Fonction pour prédire les ventes pour un mois donné
def predict_sales_for_month(year, month, model_path):
    days_in_month = calendar.monthrange(year, month)[1]
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-{days_in_month}'
    future_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    future = pd.DataFrame({'ds': future_dates})
    forecast = model.predict(future)
    total_sales = round(forecast['yhat'].sum())
    
    return total_sales

# Fonction pour comparer plusieurs modèles
def compare_models_for_month(year, month, models_folder, prices, types):
    results_list = []
    for model_file in os.listdir(models_folder):
        if model_file.endswith('.pkl'):
            model_path = os.path.join(models_folder, model_file)
            total_sales = predict_sales_for_month(year, month, model_path)
            revenue = total_sales * prices[model_file]
            product_type = types[model_file]
            results_list.append({
                'Product': model_file.replace('.pkl', ''),
                'Type': product_type,
                'Vente': total_sales,
                'CA': revenue
            })
    
    results_df = pd.DataFrame(results_list)
    return results_df

# Exemple de dictionnaire des types et des prix
types = {
    'coppa.pkl': 'Charcuterie',
    'Crème_raffermissante_pour_le_corps_Garnier.pkl': 'Produits de soin pour le corps',
    'Jambon_des_Ardennes.pkl': 'Charcuterie',
    'Jambon_de_Bayonne.pkl': 'Charcuterie',
    'Jambon_de_Luxeuil.pkl': 'Charcuterie',
    'Rillettes_doie.pkl': 'Charcuterie',
    'Saucisson_aux_noisettes.pkl': 'Charcuterie',
    'Saucisson_de_Lyon.pkl': 'Charcuterie',
    'Saucisson_à_la_pistache.pkl': 'Charcuterie',
    'Sérum_hydratant_Vichy.pkl': 'Produits de soin pour le corps'
}
prices = {
    'coppa.pkl': 1600.0,
    'Crème_raffermissante_pour_le_corps_Garnier.pkl': 2000.0,
    'Jambon_des_Ardennes.pkl': 2000.0,
    'Jambon_de_Bayonne.pkl': 1900.0,
    'Jambon_de_Luxeuil.pkl': 2000.0,
    'Rillettes_doie.pkl': 1500.0,
    'Saucisson_aux_noisettes.pkl': 1400.0,
    'Saucisson_de_Lyon.pkl': 1400.0,
    'Saucisson_à_la_pistache.pkl': 1600.0,
    'Sérum_hydratant_Vichy.pkl': 3000.0
}

# Route pour prédire les ventes et afficher les résultats dans une page HTML
@app.route("/prediction_produit", methods=['GET', 'POST'])
@login_required
def prediction_produit():
    if request.method == 'POST':
        month = int(request.form['month_value'])  # Récupérer la valeur du mois soumis
        year = 2024  # Ou récupérer l'année dynamiquement si nécessaire
        session['month'] = month
        session['year'] = year
        
        # Utilisez `year` et `month` pour appeler vos fonctions de prédiction
        df_results = compare_models_for_month(year, month, 'model', prices, types)
        df_results = df_results.sort_values(by=['Vente', 'CA'], ascending=False)
        df_results.reset_index(drop=True, inplace=True)
        prediction = df_results.to_dict(orient='records')

        # Stocker les résultats dans la session pour pouvoir les afficher après la redirection
        session['prediction'] = prediction
        
        # Créer un message flash
        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        flash_message = f"Prédiction effectuée pour le mois de {months[month-1]} {year}"
        flash(flash_message, 'success')
        
        return redirect(url_for('prediction_produit', submitted='true'))
    else:
        if 'submitted' in request.args and 'prediction' in session:
            prediction = session['prediction']
            month = session.get('month', 1)  # Default to January if not found
            year = session.get('year', 2024)
            months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
            month_name = months[month - 1]
            return render_template("admin/dash.html", prediction=prediction, month_name=month_name, year=year)
        else:
            return render_template("admin/dash.html")


#client
@app.route("/client")
@login_required
def client():
    cursor = conn.cursor()
    cursor.execute( "SELECT * FROM Client ")
    data = cursor.fetchall()
    return render_template("admin/client.html", data=data)

#suppression client
@app.route("/delete-client/<int:id_client>", methods=['POST'])
@login_required
def delete_client(id_client):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Client WHERE IdClient = ?", (id_client,))
        conn.commit()
        flash('Client supprimé avec succès!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur lors de la suppression du client: {str(e)}', 'error')  # Affichage plus détaillé de l'erreur
    finally:
        cursor.close()
    return redirect(url_for('client'))

#modifier client
@app.route("/modifier_client/<int:id_client>")
@login_required
def modifier_client(id_client):
    cursor = conn.cursor()
    try:
        # Récupérer les informations du client
        cursor.execute("SELECT NomClient, GenreClient, TelephoneClient FROM Client WHERE IdClient = ?", (id_client,))
        client_info = cursor.fetchone()
        if client_info:
            # Pré-remplir le formulaire avec les informations du client
            return render_template("admin/modif_client.html", client=client_info, client_id=id_client)
        else:
            flash("Client non trouvé.", "error")
            return redirect(url_for('client'))
    except Exception as e:
        flash(f"Erreur lors de la récupération des données: {str(e)}", 'error')
        return redirect(url_for('client'))
    finally:
        cursor.close()

#update client
@app.route("/update_client/<int:id_client>", methods=['POST'])
@login_required
def update_client(id_client):
    # Récupération des données du formulaire
    nom = request.form['nom']
    genre = request.form['genre']
    tel = request.form['tel']

    # Connexion à la base de données
    cursor = conn.cursor()
    try:
        # Mise à jour des informations du client
        cursor.execute("""
            UPDATE Client 
            SET NomClient = ?, GenreClient = ?, TelephoneClient = ?
            WHERE IdClient = ?
        """, (nom, genre, tel, id_client))
        conn.commit()
        flash('Les informations du client ont été mises à jour avec succès.', 'success')
    except Exception as e:
        # Gérer les erreurs de mise à jour
        conn.rollback()
        flash(f'Erreur lors de la mise à jour des données: {str(e)}', 'error')
    finally:
        cursor.close()
    
    # Redirection vers la page de profil du client ou une autre page appropriée
    return redirect(url_for('client', id_client=id_client))


@app.route("/recherche_client", methods=['GET'])
def recherche_client():
    query = request.args.get('q', '').strip()  # Récupérer la chaîne de recherche et supprimer les espaces superflus
    if query:
        cursor = conn.cursor()
        try:
            # Exécuter une requête SQL pour rechercher les clients par nom
            cursor.execute("SELECT * FROM Client WHERE NomClient LIKE ?", ('%' + query + '%',))
            data = cursor.fetchall()
            return render_template("admin/client.html", data=data, query=query)
        except Exception as e:
            flash(f"Erreur lors de la recherche: {str(e)}", 'error')
            return redirect(url_for('client'))  # ou toute autre page appropriée
        finally:
            cursor.close()
    else:
        flash("Veuillez entrer un terme de recherche.", 'warning')
        return redirect(url_for('client'))


#vendeur
@app.route("/vendeur")
@login_required
def vendeur():
    cursor = conn.cursor()
    cursor.execute( "SELECT * FROM Vendeur ")
    data = cursor.fetchall()
    return render_template("admin/vendeur.html", data=data)

#suppression vendeur
@app.route("/delete-vendeur/<int:id_vendeur>", methods=['POST'])
@login_required
def delete_vendeur(id_vendeur):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Vendeur WHERE IdVendeur = ?", (id_vendeur,))
        conn.commit()
        flash('Vendeur supprimé avec succès!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur lors de la suppression du vendeur: {str(e)}', 'error')  # Affichage plus détaillé de l'erreur
    finally:
        cursor.close()
    return redirect(url_for('vendeur'))


#modifier vendeur
@app.route("/modifier_vendeur/<int:id_vendeur>")
@login_required
def modifier_vendeur(id_vendeur):
    cursor = conn.cursor()
    try:
        # Récupérer les informations du client
        cursor.execute("SELECT NomVendeur, PrenomVendeur, DateNaissance, lieu_hab_rep FROM Vendeur WHERE IdVendeur = ?", (id_vendeur,))
        vendeur_info = cursor.fetchone()
        if vendeur_info:
            # Pré-remplir le formulaire avec les informations du client
            return render_template("admin/modif_vendeur.html", vendeur=vendeur_info, vendeur_id=id_vendeur)
        else:
            flash("Vendeur non trouvé.", "error")
            return redirect(url_for('vendeur'))
    except Exception as e:
        flash(f"Erreur lors de la récupération des données: {str(e)}", 'error')
        return redirect(url_for('vendeur'))
    finally:
        cursor.close()


#update vendeur
@app.route("/update_vendeur/<int:id_vendeur>", methods=['POST'])
@login_required
def update_vendeur(id_vendeur):
    # Récupération des données du formulaire
    nom = request.form['nom']
    prenom = request.form['prenom']
    date_naissance = request.form['date_naissance']
    lieu_habitation = request.form['lieu_habitation']

    # Connexion à la base de données
    cursor = conn.cursor()
    try:
        # Mise à jour des informations du vendeur
        cursor.execute("""
            UPDATE Vendeur 
            SET NomVendeur = ?, PrenomVendeur = ?,DateNaissance = ? ,lieu_hab_rep = ?
            WHERE IdVendeur = ?
        """, (nom, prenom, date_naissance,lieu_habitation, id_vendeur))
        conn.commit()
        flash('Les informations du vendeur ont été mises à jour avec succès.', 'success')
    except Exception as e:
        # Gérer les erreurs de mise à jour
        conn.rollback()
        flash(f'Erreur lors de la mise à jour des données: {str(e)}', 'error')
    finally:
        cursor.close()
    
    # Redirection vers la page de profil du vendeur ou une autre page appropriée
    return redirect(url_for('vendeur', id_vendeur=id_vendeur))

@app.route("/recherche_vendeur", methods=['GET'])
def recherche_vendeur():
    query = request.args.get('q', '').strip()  # Récupérer la chaîne de recherche et supprimer les espaces superflus
    if query:
        cursor = conn.cursor()
        try:
            # Exécuter une requête SQL pour rechercher les vendeurs par nom
            cursor.execute("SELECT * FROM Vendeur WHERE NomVendeur LIKE ?", ('%' + query + '%',))
            data = cursor.fetchall()
            return render_template("admin/vendeur.html", data=data, query=query)
        except Exception as e:
            flash(f"Erreur lors de la recherche: {str(e)}", 'error')
            return redirect(url_for('vendeur'))  # ou toute autre page appropriée
        finally:
            cursor.close()
    else:
        flash("Veuillez entrer un terme de recherche.", 'warning')
        return redirect(url_for('vendeur'))

@app.route("/gestionnaire")
@login_required
def gestionnaire():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Gestionnaire")
    data = cursor.fetchall()
    number_of_gestionnaires = len(data)  # Calculer le nombre de gestionnaires
    return render_template("admin/gestionnaire.html", data=data, count=number_of_gestionnaires)


#suppression gestionnaire
@app.route("/delete-gestionnaire/<int:id_gestionnaire>", methods=['POST'])
@login_required
def delete_gestionnaire(id_gestionnaire):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Gestionnaire WHERE IdGestionnaire = ?", (id_gestionnaire,))
        conn.commit()
        flash('Gestionnaire supprimé avec succès!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur lors de la suppression du gestionnaire: {str(e)}', 'error')  # Affichage plus détaillé de l'erreur
    finally:
        cursor.close()
    return redirect(url_for('gestionnaire'))

#modifier gestionnaire
@app.route("/modifier_gestionnaire/<int:id_gestionnaire>")
@login_required
def modifier_gestionnaire(id_gestionnaire):
    cursor = conn.cursor()
    try:
        # Récupérer les informations du gestionnaire
        cursor.execute("SELECT NomGestionnaire, PrenomGestionnaire, DateNaissance, lieu_hab_rep FROM Gestionnaire WHERE IdGestionnaire = ?", (id_gestionnaire,))
        gestionnaire_info = cursor.fetchone()
        if gestionnaire_info:
            # Pré-remplir le formulaire avec les informations du gestionnaire
            return render_template("admin/modif_gestionnaire.html", gestionnaire=gestionnaire_info, gestionnaire_id=id_gestionnaire)
        else:
            flash("Gestionnaire non trouvé.", "error")
            return redirect(url_for('gestionnaire'))
    except Exception as e:
        flash(f"Erreur lors de la récupération des données: {str(e)}", 'error')
        return redirect(url_for('gestionnaire'))
    finally:
        cursor.close()

#update gestionnaire
@app.route("/update_gestionnaire/<int:id_gestionnaire>", methods=['POST'])
@login_required
def update_gestionnaire(id_gestionnaire):
    # Récupération des données du formulaire
    nom = request.form['nom']
    prenom = request.form['prenom']
    date_naissance = request.form['date_naissance']
    lieu_habitation = request.form['lieu_habitation']

    # Connexion à la base de données
    cursor = conn.cursor()
    try:
        # Mise à jour des informations du gestionnaire
        cursor.execute("""
            UPDATE Gestionnaire 
            SET NomGestionnaire = ?, PrenomGestionnaire = ?,DateNaissance = ? ,lieu_hab_rep = ?
            WHERE IdGestionnaire = ?
        """, (nom, prenom, date_naissance,lieu_habitation, id_gestionnaire))
        conn.commit()
        flash('Les informations du gestionnaire ont été mises à jour avec succès.', 'success')
    except Exception as e:
        # Gérer les erreurs de mise à jour
        conn.rollback()
        flash(f'Erreur lors de la mise à jour des données: {str(e)}', 'error')
    finally:
        cursor.close()
    
    # Redirection vers la page de profil du gestionnaire ou une autre page appropriée
    return redirect(url_for('gestionnaire', id_gestionnaire=id_gestionnaire))

@app.route("/recherche_gestionnaire", methods=['GET'])
def recherche_gestionnaire():
    query = request.args.get('q', '').strip()  # Récupérer la chaîne de recherche et supprimer les espaces superflus
    if query:
        cursor = conn.cursor()
        try:
            # Exécuter une requête SQL pour rechercher les gestionnaires par nom
            cursor.execute("SELECT * FROM Gestionnaire WHERE NomGestionnaire LIKE ?", ('%' + query + '%',))
            data = cursor.fetchall()
            return render_template("admin/gestionnaire.html", data=data, query=query)
        except Exception as e:
            flash(f"Erreur lors de la recherche: {str(e)}", 'error')
            return redirect(url_for('gestionnaire'))  # ou toute autre page appropriée
        finally:
            cursor.close()
    else:
        flash("Veuillez entrer un terme de recherche.", 'warning')
        return redirect(url_for('gestionnaire'))











##########Dashbord_vendeur############
@app.route("/dash_vendeur")
@login_required
def dash_vendeur():
    user_id = session.get('user_id')
    cursor = conn.cursor()
    cursor.execute( "SELECT * FROM Vendeur WHERE IdUser = ?", user_id)
    data = cursor.fetchall()
    conn.commit()
    return render_template("vendeur/dash_vendeur.html", user_id =user_id, data=data)










##########Dashbord_gestionnaire############
@app.route("/dash_gestionnaire")
@login_required
def dash_gestionnaire():
    user_id = session.get('user_id')
    cursor = conn.cursor()
    cursor.execute( "SELECT * FROM Gestionnaire WHERE IdUser = ?", user_id)
    data = cursor.fetchall()
    conn.commit()
    return render_template("gestionnaire/dash_gestionnaire.html", user_id =user_id, data=data)








if __name__ == "__main__":
    app.secret_key = 'admin123'
    # socketio.run(app, debug=True)
    app.run(debug=True)
