#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de génération de réclamations synthétiques pour le POC de chatbot IA AssurSanté.
Ce script génère des réclamations réalistes pour les clients existants dans la base de données.
"""

import json
import random
import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
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
NB_RECLAMATIONS_MIN_PAR_CLIENT = 0  # Certains clients n'ont pas de réclamations
NB_RECLAMATIONS_MAX_PAR_CLIENT = 3

# Types de réclamations disponibles
TYPES_RECLAMATIONS = [
    "Remboursement",
    "Contestation",
    "Information",
    "Modification contrat",
    "Résiliation",
    "Prise en charge",
    "Délai traitement",
    "Erreur facturation"
]

# Statuts de réclamation disponibles
STATUTS_RECLAMATION = [
    "Nouveau",
    "En cours",
    "En attente",
    "Traitée",
    "Clôturée",
    "Rejetée"
]

# Agents de traitement
AGENTS_TRAITEMENT = [
    "Jean Dupont",
    "Marie Martin",
    "Philippe Dubois",
    "Sophie Bernard",
    "Thomas Leroy"
]

# Descriptions de réclamations par type
DESCRIPTIONS_RECLAMATIONS = {
    "Remboursement": [
        "Je n'ai toujours pas reçu le remboursement de ma consultation chez le spécialiste du {date}.",
        "Le montant remboursé pour mes soins dentaires est inférieur à ce qui est prévu dans mon contrat.",
        "Je souhaite contester le refus de remboursement pour ma séance de kinésithérapie du {date}.",
        "Le délai de remboursement de mes frais d'optique dépasse les 15 jours prévus dans mon contrat."
    ],
    "Contestation": [
        "Je conteste le montant de ma cotisation qui a augmenté sans justification.",
        "Le taux de remboursement appliqué ne correspond pas à celui indiqué dans mon contrat {contrat}.",
        "Je souhaite contester le refus de prise en charge pour mon hospitalisation du {date}.",
        "Le plafond annuel appliqué à mes remboursements dentaires est incorrect."
    ],
    "Information": [
        "Je souhaite obtenir des informations sur les garanties de mon contrat {contrat}.",
        "Pourriez-vous m'expliquer les modalités de remboursement pour les médecines douces ?",
        "Je voudrais connaître les démarches pour ajouter mon conjoint à mon contrat santé.",
        "Quelles sont les pièces justificatives nécessaires pour le remboursement des lunettes ?"
    ],
    "Modification contrat": [
        "Je souhaite modifier mon niveau de garantie pour passer au niveau supérieur.",
        "Suite à mon déménagement, je dois mettre à jour mon adresse sur mon contrat.",
        "Je voudrais ajouter mon enfant né le {date} à mon contrat famille.",
        "Suite à mon changement de situation professionnelle, je souhaite adapter mes garanties."
    ],
    "Résiliation": [
        "Je souhaite résilier mon contrat {contrat} car j'ai souscrit une mutuelle entreprise.",
        "Suite à mon départ à l'étranger, je dois résilier mon contrat santé.",
        "Je demande la résiliation de mon contrat suite à une augmentation excessive de ma cotisation.",
        "N'ayant plus besoin de cette couverture spécifique, je souhaite résilier ce contrat."
    ],
    "Prise en charge": [
        "Je souhaite obtenir une prise en charge pour mon hospitalisation prévue le {date}.",
        "Ma demande de prise en charge pour mes soins dentaires n'a pas été traitée.",
        "J'ai besoin d'une prise en charge urgente pour une intervention chirurgicale.",
        "Le centre hospitalier me demande une attestation de prise en charge avant mon admission."
    ],
    "Délai traitement": [
        "Ma demande de remboursement du {date} est en attente depuis plus de 3 semaines.",
        "Je n'ai reçu aucune réponse à ma demande de prise en charge envoyée il y a 10 jours.",
        "Le traitement de mon dossier de changement de garantie prend un temps anormalement long.",
        "Malgré plusieurs relances, ma réclamation du {date} n'a toujours pas été traitée."
    ],
    "Erreur facturation": [
        "J'ai été prélevé deux fois pour ma cotisation du mois de {mois}.",
        "Le montant prélevé ne correspond pas à celui indiqué dans mon échéancier.",
        "Une erreur s'est glissée dans le calcul de ma cotisation annuelle.",
        "Je constate une incohérence entre le montant facturé et les garanties souscrites."
    ]
}

def get_clients_from_db():
    """Récupère les clients et leurs contrats depuis la base de données."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupération des clients
        cursor.execute("SELECT * FROM clients")
        clients = cursor.fetchall()
        
        # Pour chaque client, récupération de ses contrats
        for client in clients:
            cursor.execute("SELECT * FROM contrats WHERE client_id = %s", (client['id'],))
            client['contrats'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return clients
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des clients: {e}")
        return []

def generate_reclamation(client, contrat):
    """Génère une réclamation synthétique pour un client et un contrat donnés."""
    type_reclamation = random.choice(TYPES_RECLAMATIONS)
    statut = random.choice(STATUTS_RECLAMATION)
    
    # Date de réclamation entre la date de début du contrat et aujourd'hui
    date_debut_contrat = datetime.datetime.strptime(contrat['date_debut'], '%Y-%m-%d')
    date_reclamation = fake.date_between(start_date=date_debut_contrat, end_date='today')
    
    # Description de la réclamation
    description_template = random.choice(DESCRIPTIONS_RECLAMATIONS[type_reclamation])
    
    # Remplacement des variables dans le template
    description = description_template.format(
        date=fake.date_between(start_date=date_debut_contrat, end_date=date_reclamation).strftime('%d/%m/%Y'),
        contrat=contrat['numero_contrat'],
        mois=fake.month_name()
    )
    
    # Montant demandé (uniquement pour certains types de réclamations)
    montant_demande = None
    if type_reclamation in ["Remboursement", "Contestation", "Erreur facturation"]:
        montant_demande = round(random.uniform(20, 500), 2)
    
    # Date de traitement et agent (uniquement pour les réclamations traitées ou clôturées)
    date_traitement = None
    agent_traitement = None
    
    if statut in ["Traitée", "Clôturée", "Rejetée"]:
        date_traitement = fake.date_between(start_date=date_reclamation, end_date='today').strftime('%Y-%m-%d')
        agent_traitement = random.choice(AGENTS_TRAITEMENT)
    
    # Génération du numéro de réclamation
    annee = date_reclamation.year
    numero_reclamation = f"REC-{annee}-{fake.unique.random_number(digits=3):03d}"
    
    # Commentaires (uniquement pour les réclamations traitées ou clôturées)
    commentaires = None
    if statut in ["Traitée", "Clôturée", "Rejetée"]:
        if statut == "Traitée":
            commentaires = random.choice([
                "Réclamation traitée avec succès. Remboursement effectué.",
                "Dossier complet, remboursement validé.",
                "Prise en charge accordée selon les garanties du contrat.",
                "Modification effectuée comme demandé par le client."
            ])
        elif statut == "Clôturée":
            commentaires = random.choice([
                "Dossier clôturé après résolution du problème.",
                "Réclamation résolue à la satisfaction du client.",
                "Clôture suite à l'accord trouvé avec le client.",
                "Dossier finalisé après traitement complet."
            ])
        elif statut == "Rejetée":
            commentaires = random.choice([
                "Réclamation rejetée car hors garanties du contrat.",
                "Demande non conforme aux conditions générales.",
                "Justificatifs insuffisants pour traiter la demande.",
                "Délai de déclaration dépassé."
            ])
    
    reclamation = {
        'client_id': client['id'],
        'contrat_id': contrat['id'],
        'numero_reclamation': numero_reclamation,
        'date_reclamation': date_reclamation.strftime('%Y-%m-%d'),
        'type_reclamation': type_reclamation,
        'description': description,
        'montant_demande': montant_demande,
        'statut': statut,
        'date_traitement': date_traitement,
        'agent_traitement': agent_traitement,
        'commentaires': commentaires
    }
    
    return reclamation

def insert_reclamations_to_db(reclamations):
    """Insère les réclamations dans la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        for reclamation in reclamations:
            cursor.execute("""
                INSERT INTO reclamations 
                (client_id, contrat_id, numero_reclamation, date_reclamation, 
                type_reclamation, description, montant_demande, statut, 
                date_traitement, agent_traitement, commentaires)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reclamation['client_id'],
                reclamation['contrat_id'],
                reclamation['numero_reclamation'],
                reclamation['date_reclamation'],
                reclamation['type_reclamation'],
                reclamation['description'],
                reclamation['montant_demande'],
                reclamation['statut'],
                reclamation['date_traitement'],
                reclamation['agent_traitement'],
                reclamation['commentaires']
            ))
        
        conn.commit()
        print(f"✅ {len(reclamations)} réclamations ont été insérées avec succès dans la base de données.")
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de l'insertion des réclamations: {e}")
    
    finally:
        cursor.close()
        conn.close()

def save_reclamations_to_json(reclamations, filename='reclamations_data.json'):
    """Sauvegarde les réclamations générées dans un fichier JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reclamations, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Les réclamations ont été sauvegardées dans {filename}")

def main():
    """Fonction principale pour générer et sauvegarder les réclamations."""
    print("Récupération des clients depuis la base de données...")
    clients = get_clients_from_db()
    
    if not clients:
        print("❌ Aucun client trouvé dans la base de données. Veuillez d'abord exécuter generate_clients.py.")
        return
    
    print(f"Génération de réclamations pour {len(clients)} clients...")
    
    reclamations = []
    for client in clients:
        # Certains clients n'ont pas de réclamations
        nb_reclamations = random.randint(NB_RECLAMATIONS_MIN_PAR_CLIENT, NB_RECLAMATIONS_MAX_PAR_CLIENT)
        
        if nb_reclamations > 0 and client['contrats']:
            for _ in range(nb_reclamations):
                # Sélection aléatoire d'un contrat du client
                contrat = random.choice(client['contrats'])
                reclamation = generate_reclamation(client, contrat)
                reclamations.append(reclamation)
    
    print(f"✅ {len(reclamations)} réclamations générées.")
    
    # Sauvegarde des données au format JSON
    save_reclamations_to_json(reclamations)
    
    # Insertion des données dans PostgreSQL
    try_db = input("Voulez-vous insérer les réclamations dans PostgreSQL? (o/n): ").lower()
    if try_db == 'o':
        insert_reclamations_to_db(reclamations)

if __name__ == "__main__":
    main()
