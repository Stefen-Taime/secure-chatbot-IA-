#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de génération de données clients synthétiques pour le POC de chatbot IA AssurSanté.
Ce script génère des profils clients réalistes avec leurs informations personnelles et contrats d'assurance.
"""

import json
import random
import datetime
import os
import psycopg2
from faker import Faker
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv('../docker/.env')

# Configuration de Faker pour générer des données en français
fake = Faker(['fr_FR'])

# Paramètres de connexion à la base de données
DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'assursante_db'),
    'user': os.getenv('POSTGRES_USER', 'assursante'),
    'password': os.getenv('POSTGRES_PASSWORD', 'secure_password_123')
}

# Constantes pour la génération de données
NB_CLIENTS = 100
NB_CONTRATS_MIN = 1
NB_CONTRATS_MAX = 3

# Types de contrats disponibles
TYPES_CONTRATS = [
    "Santé Individuelle",
    "Santé Famille",
    "Santé Senior",
    "Prévoyance",
    "Hospitalisation",
    "Dentaire Plus",
    "Optique Premium",
    "Maternité"
]

# Niveaux de couverture disponibles
NIVEAUX_COUVERTURE = [
    "Économique",
    "Standard",
    "Confort",
    "Premium",
    "Excellence"
]

# Statuts de contrat disponibles
STATUTS_CONTRAT = [
    "Actif",
    "En attente",
    "Suspendu",
    "Résilié"
]

def generate_numero_securite_sociale():
    """Génère un numéro de sécurité sociale français valide."""
    sexe = random.choice([1, 2])  # 1 pour homme, 2 pour femme
    annee = random.randint(0, 99)
    mois = random.randint(1, 12)
    departement = random.randint(1, 95)
    if departement == 20:  # Remplacer 20 par 2A ou 2B pour la Corse
        departement = random.choice(['2A', '2B'])
    commune = random.randint(1, 999)
    ordre = random.randint(1, 999)
    
    # Formatage du numéro
    if isinstance(departement, str):
        num = f"{sexe}{annee:02d}{mois:02d}{departement}{commune:03d}{ordre:03d}"
    else:
        num = f"{sexe}{annee:02d}{mois:02d}{departement:02d}{commune:03d}{ordre:03d}"
    
    # Calcul de la clé (simplifié pour l'exemple)
    cle = 97 - (int(num) % 97)
    
    return f"{num}{cle:02d}"

def generate_client():
    """Génère un profil client synthétique."""
    sexe = random.choice(['M', 'F'])
    if sexe == 'M':
        prenom = fake.first_name_male()
    else:
        prenom = fake.first_name_female()
    
    nom = fake.last_name()
    date_naissance = fake.date_of_birth(minimum_age=18, maximum_age=90)
    
    client = {
        'nom': nom,
        'prenom': prenom,
        'date_naissance': date_naissance.strftime('%Y-%m-%d'),
        'email': fake.email(),
        'telephone': fake.phone_number(),
        'adresse': fake.street_address(),
        'code_postal': fake.postcode(),
        'ville': fake.city(),
        'numero_securite_sociale': generate_numero_securite_sociale(),
        'contrats': []
    }
    
    # Génération des contrats pour ce client
    nb_contrats = random.randint(NB_CONTRATS_MIN, NB_CONTRATS_MAX)
    for _ in range(nb_contrats):
        contrat = generate_contrat()
        client['contrats'].append(contrat)
    
    return client

def generate_contrat():
    """Génère un contrat d'assurance synthétique."""
    type_contrat = random.choice(TYPES_CONTRATS)
    niveau_couverture = random.choice(NIVEAUX_COUVERTURE)
    statut = random.choice(STATUTS_CONTRAT)
    
    # Pondération des montants selon le niveau de couverture
    if niveau_couverture == "Économique":
        montant_base = random.uniform(30, 60)
    elif niveau_couverture == "Standard":
        montant_base = random.uniform(60, 100)
    elif niveau_couverture == "Confort":
        montant_base = random.uniform(100, 150)
    elif niveau_couverture == "Premium":
        montant_base = random.uniform(150, 200)
    else:  # Excellence
        montant_base = random.uniform(200, 300)
    
    # Ajustement selon le type de contrat
    if type_contrat == "Santé Famille":
        montant_base *= 2.2
    elif type_contrat == "Santé Senior":
        montant_base *= 1.5
    elif type_contrat == "Prévoyance":
        montant_base *= 0.8
    elif type_contrat == "Hospitalisation":
        montant_base *= 0.7
    elif type_contrat == "Dentaire Plus":
        montant_base *= 0.9
    elif type_contrat == "Optique Premium":
        montant_base *= 0.85
    elif type_contrat == "Maternité":
        montant_base *= 1.3
    
    # Génération des dates
    date_debut = fake.date_between(start_date='-3y', end_date='today')
    
    # 80% des contrats actifs ont une date de fin dans le futur
    if statut == "Actif" and random.random() < 0.8:
        date_fin = fake.date_between(start_date='+1m', end_date='+2y')
    else:
        # Pour les contrats résiliés ou certains actifs, date de fin dans le passé ou proche
        date_fin = fake.date_between(start_date=date_debut, end_date='+1y')
    
    # Génération du numéro de contrat
    annee = date_debut.year
    numero_contrat = f"CONT-{annee}-{fake.unique.random_number(digits=3):03d}"
    
    contrat = {
        'numero_contrat': numero_contrat,
        'type_contrat': type_contrat,
        'date_debut': date_debut.strftime('%Y-%m-%d'),
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'montant_cotisation': round(montant_base, 2),
        'niveau_couverture': niveau_couverture,
        'statut': statut
    }
    
    return contrat

def insert_clients_to_db(clients):
    """Insère les clients et leurs contrats dans la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        for client in clients:
            # Insertion du client
            cursor.execute("""
                INSERT INTO clients 
                (nom, prenom, date_naissance, email, telephone, adresse, code_postal, ville, numero_securite_sociale)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                client['nom'], 
                client['prenom'], 
                client['date_naissance'], 
                client['email'], 
                client['telephone'], 
                client['adresse'], 
                client['code_postal'], 
                client['ville'], 
                client['numero_securite_sociale']
            ))
            
            client_id = cursor.fetchone()[0]
            
            # Insertion des contrats
            for contrat in client['contrats']:
                cursor.execute("""
                    INSERT INTO contrats 
                    (client_id, numero_contrat, type_contrat, date_debut, date_fin, 
                    montant_cotisation, niveau_couverture, statut)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    client_id,
                    contrat['numero_contrat'],
                    contrat['type_contrat'],
                    contrat['date_debut'],
                    contrat['date_fin'],
                    contrat['montant_cotisation'],
                    contrat['niveau_couverture'],
                    contrat['statut']
                ))
        
        conn.commit()
        print(f"✅ {len(clients)} clients et leurs contrats ont été insérés avec succès dans la base de données.")
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de l'insertion des données: {e}")
    
    finally:
        cursor.close()
        conn.close()

def save_clients_to_json(clients, filename='clients_data.json'):
    """Sauvegarde les clients générés dans un fichier JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Les données ont été sauvegardées dans {filename}")

def main():
    """Fonction principale pour générer et sauvegarder les données clients."""
    print(f"Génération de {NB_CLIENTS} clients synthétiques...")
    
    clients = []
    for _ in range(NB_CLIENTS):
        client = generate_client()
        clients.append(client)
    
    # Sauvegarde des données au format JSON
    save_clients_to_json(clients)
    
    # Insertion des données dans PostgreSQL
    try_db = input("Voulez-vous insérer les données dans PostgreSQL? (o/n): ").lower()
    if try_db == 'o':
        insert_clients_to_db(clients)

if __name__ == "__main__":
    main()
