#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de vectorisation de la base de connaissances pour le POC de chatbot IA AssurSanté.
Ce script crée une base de connaissances vectorielle à partir de documents d'assurance santé.
"""

import os
import json
import numpy as np
import random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv('../docker/.env')

# Configuration
VECTOR_DB_HOST = os.getenv('VECTOR_DB_HOST', 'localhost')
COLLECTION_NAME = "knowledge_base"
VECTOR_SIZE = 384  # Dimension des vecteurs pour le modèle all-MiniLM-L6-v2
BATCH_SIZE = 100

# Modèle de vectorisation
MODEL_NAME = "all-MiniLM-L6-v2"  # Modèle léger et performant

# Base de connaissances - Documents d'assurance santé
KNOWLEDGE_BASE = [
    {
        "title": "Remboursement des consultations médicales",
        "category": "Remboursements",
        "content": """
Les consultations médicales sont remboursées selon les conditions suivantes :
- Médecin généraliste conventionné secteur 1 : remboursement à 100% du tarif de convention
- Médecin généraliste conventionné secteur 2 : remboursement à 100% du tarif de convention + dépassements selon niveau de garantie
- Médecin spécialiste conventionné secteur 1 : remboursement à 100% du tarif de convention
- Médecin spécialiste conventionné secteur 2 : remboursement à 100% du tarif de convention + dépassements selon niveau de garantie

Les délais de remboursement standards sont de 3 à 5 jours ouvrés à compter de la réception des justificatifs complets.
        """
    },
    {
        "title": "Remboursement des frais d'hospitalisation",
        "category": "Remboursements",
        "content": """
Les frais d'hospitalisation sont pris en charge selon les modalités suivantes :
- Forfait journalier hospitalier : couverture à 100% sans limitation de durée
- Frais de séjour : remboursement à 100% du tarif conventionnel
- Chambre particulière : prise en charge selon le niveau de garantie (Économique: non couvert, Standard: 50€/jour, Confort: 70€/jour, Premium: 90€/jour, Excellence: 120€/jour)
- Frais d'accompagnant : prise en charge pour les enfants de moins de 16 ans et les personnes de plus de 70 ans

Une demande de prise en charge hospitalière doit être effectuée au moins 5 jours avant la date d'hospitalisation programmée.
        """
    },
    {
        "title": "Remboursement des soins dentaires",
        "category": "Remboursements",
        "content": """
Les soins dentaires sont remboursés selon la grille suivante :
- Soins dentaires : remboursement à 100% du tarif de convention
- Prothèses dentaires : remboursement selon barème (Économique: 100% BR, Standard: 150% BR, Confort: 200% BR, Premium: 300% BR, Excellence: 400% BR)
- Orthodontie : remboursement selon barème (Économique: 100% BR, Standard: 150% BR, Confort: 200% BR, Premium: 250% BR, Excellence: 300% BR)
- Implantologie : forfait annuel selon niveau de garantie

Les plafonds annuels de remboursement dentaire sont les suivants :
- Économique: 700€/an
- Standard: 1000€/an
- Confort: 1500€/an
- Premium: 2000€/an
- Excellence: 2500€/an
        """
    },
    {
        "title": "Remboursement des frais d'optique",
        "category": "Remboursements",
        "content": """
Les équipements optiques (monture + verres) sont pris en charge selon les conditions suivantes :
- Renouvellement possible tous les 2 ans pour les adultes (sauf changement de correction)
- Renouvellement possible tous les ans pour les enfants de moins de 16 ans
- Forfaits de remboursement selon le niveau de garantie :
  * Économique: 100€ (dont 50€ max pour la monture)
  * Standard: 200€ (dont 75€ max pour la monture)
  * Confort: 300€ (dont 100€ max pour la monture)
  * Premium: 400€ (dont 100€ max pour la monture)
  * Excellence: 500€ (dont 100€ max pour la monture)

Les lentilles sont prises en charge à hauteur d'un forfait annuel selon le niveau de garantie.
        """
    },
    {
        "title": "Procédure de demande de remboursement",
        "category": "Procédures",
        "content": """
Pour obtenir un remboursement, veuillez suivre la procédure suivante :
1. Conservez tous les justificatifs originaux (factures, prescriptions médicales, etc.)
2. Vérifiez que la Sécurité Sociale a bien traité votre demande (si applicable)
3. Transmettez votre demande via l'espace client en ligne ou par courrier
4. Joignez les pièces justificatives suivantes :
   - Facture acquittée détaillée
   - Prescription médicale (si nécessaire)
   - Décompte de la Sécurité Sociale (si applicable)

Le délai de traitement standard est de 3 à 5 jours ouvrés à compter de la réception d'un dossier complet.
Les demandes de remboursement doivent être effectuées dans un délai maximum de 2 ans à compter de la date des soins.
        """
    },
    {
        "title": "Procédure de demande de prise en charge hospitalière",
        "category": "Procédures",
        "content": """
Pour obtenir une prise en charge hospitalière, veuillez suivre la procédure suivante :
1. Contactez notre service de prise en charge au moins 5 jours avant la date d'hospitalisation programmée
2. Fournissez les informations suivantes :
   - Nom et prénom de l'assuré
   - Numéro d'adhérent
   - Date d'entrée prévue
   - Nom et adresse de l'établissement hospitalier
   - Service d'admission
   - Nature de l'hospitalisation (médicale, chirurgicale, ambulatoire)

Une attestation de prise en charge sera envoyée directement à l'établissement hospitalier.
Pour les hospitalisations d'urgence, la demande peut être effectuée dans les 48h suivant l'admission.
        """
    },
    {
        "title": "Procédure de déclaration d'un changement de situation",
        "category": "Procédures",
        "content": """
Tout changement de situation doit être déclaré dans un délai de 30 jours. Les changements concernés sont :
- Changement d'adresse
- Changement de coordonnées bancaires
- Changement de situation familiale (mariage, naissance, divorce, décès)
- Changement de situation professionnelle

Pour déclarer un changement, vous pouvez :
1. Utiliser votre espace client en ligne
2. Contacter notre service client par téléphone
3. Envoyer un courrier avec les justificatifs nécessaires

Les justificatifs à fournir dépendent du type de changement (certificat de mariage, acte de naissance, etc.).
        """
    },
    {
        "title": "Procédure de résiliation de contrat",
        "category": "Procédures",
        "content": """
La résiliation de votre contrat peut être effectuée dans les cas suivants :
- À l'échéance annuelle, avec un préavis de 2 mois
- En cas de changement de situation (mariage, divorce, mutation professionnelle)
- En cas d'affiliation à un contrat collectif obligatoire
- À tout moment après la première année de souscription (Loi Hamon)

Pour résilier votre contrat, vous devez :
1. Envoyer une lettre recommandée avec accusé de réception
2. Joindre les justificatifs nécessaires selon le motif de résiliation
3. Préciser la date souhaitée de fin de contrat

La résiliation prendra effet à la date indiquée dans votre courrier, sous réserve du respect des conditions contractuelles.
        """
    },
    {
        "title": "Niveaux de garantie et couvertures",
        "category": "Contrats",
        "content": """
AssurSanté propose 5 niveaux de garantie adaptés à vos besoins :

1. Économique :
   - Couverture des soins essentiels
   - Remboursements au tarif de convention
   - Plafonds annuels limités

2. Standard :
   - Couverture équilibrée
   - Remboursements à 150% du tarif de convention
   - Plafonds annuels intermédiaires

3. Confort :
   - Bonne couverture des dépassements d'honoraires
   - Remboursements à 200% du tarif de convention
   - Plafonds annuels confortables

4. Premium :
   - Couverture étendue
   - Remboursements à 300% du tarif de convention
   - Plafonds annuels élevés
   - Inclut des services additionnels

5. Excellence :
   - Couverture optimale
   - Remboursements à 400% du tarif de convention
   - Plafonds annuels très élevés
   - Inclut tous les services additionnels
   - Assistance internationale
        """
    },
    {
        "title": "Options et garanties complémentaires",
        "category": "Contrats",
        "content": """
En complément de votre garantie principale, vous pouvez souscrire aux options suivantes :

1. Option Bien-être :
   - Médecines douces (ostéopathie, acupuncture, chiropractie)
   - Cures thermales
   - Vaccins non remboursés par la Sécurité Sociale
   - Forfait prévention (sevrage tabagique, diététique)

2. Option Famille :
   - Forfait naissance/adoption
   - Forfait procréation médicalement assistée
   - Forfait contraception
   - Consultation de psychologie pour enfants

3. Option Senior :
   - Renfort audioprothèses
   - Forfait autonomie (aménagement du domicile)
   - Téléassistance
   - Bilan mémoire

4. Option Hospitalisation+ :
   - Chambre particulière améliorée
   - Confort hospitalier (TV, téléphone, wifi)
   - Assistance à domicile renforcée
   - Transport médical étendu
        """
    },
    {
        "title": "Délais de carence et limitations",
        "category": "Contrats",
        "content": """
Les délais de carence suivants s'appliquent à partir de la date d'effet du contrat :
- Soins courants : pas de délai de carence
- Hospitalisation : 3 mois (sauf accident)
- Dentaire : 6 mois
- Optique : 6 mois
- Maternité : 10 mois

Limitations spécifiques :
- Chambre particulière : limitée à 60 jours par an en psychiatrie
- Médecines douces : limitées à 4 séances par an et par bénéficiaire
- Implants dentaires : limités à 2 par an et par bénéficiaire
- Cures thermales : limitées à une cure par an et par bénéficiaire

Ces délais de carence peuvent être supprimés en cas de mutation depuis un autre organisme complémentaire sans interruption de couverture.
        """
    },
    {
        "title": "Services d'assistance et prévention",
        "category": "Services",
        "content": """
Tous nos contrats incluent les services d'assistance suivants :
- Assistance hospitalisation : aide-ménagère, garde d'enfants, portage de repas
- Assistance au quotidien : conseil médical téléphonique 24h/24
- Rapatriement médical en cas d'accident ou maladie à l'étranger
- Second avis médical pour les pathologies graves

Nos programmes de prévention comprennent :
- Bilan de santé annuel
- Coaching santé personnalisé
- Ateliers prévention (nutrition, activité physique, gestion du stress)
- Dépistages spécifiques selon l'âge et les facteurs de risque

Les niveaux Premium et Excellence bénéficient en plus :
- Conciergerie médicale
- Téléconsultation médicale illimitée
- Coach sportif à domicile
- Bilan nutritionnel personnalisé
        """
    },
    {
        "title": "Tiers payant et réseaux de soins",
        "category": "Services",
        "content": """
Le tiers payant vous permet d'être dispensé d'avance de frais chez les professionnels de santé. Il s'applique :
- Automatiquement en pharmacie
- Chez les professionnels de santé partenaires sur présentation de votre carte de tiers payant
- Dans tous les hôpitaux et cliniques conventionnés

Notre réseau de soins partenaires vous garantit :
- Des tarifs négociés (jusqu'à -40% sur les équipements optiques)
- Un contrôle qualité des prestations
- Une réduction du reste à charge
- Un tiers payant systématique

Le réseau comprend plus de 8000 professionnels partenaires :
- 3500 opticiens
- 3000 dentistes
- 1000 audioprothésistes
- 500 ostéopathes et chiropracteurs
        """
    },
    {
        "title": "Espace client et services digitaux",
        "category": "Services",
        "content": """
Votre espace client en ligne vous permet de :
- Consulter vos remboursements en temps réel
- Télécharger vos relevés de prestations
- Effectuer vos demandes de remboursement
- Obtenir une prise en charge hospitalière
- Mettre à jour vos informations personnelles
- Télécharger votre carte de tiers payant
- Contacter directement nos conseillers

L'application mobile AssurSanté vous offre également :
- L'envoi de justificatifs par photo
- La géolocalisation des professionnels de santé partenaires
- L'accès à votre carte de tiers payant dématérialisée
- Des notifications en temps réel pour vos remboursements
- La prise de rendez-vous médicaux en ligne
- L'accès à la téléconsultation médicale
        """
    },
    {
        "title": "Gestion des réclamations",
        "category": "Services",
        "content": """
Pour toute réclamation concernant votre contrat ou vos remboursements, vous pouvez :
1. Contacter notre service client par téléphone au 01 XX XX XX XX (du lundi au vendredi de 9h à 18h)
2. Utiliser le formulaire de réclamation dans votre espace client
3. Envoyer un courrier à notre service réclamations

Notre engagement qualité :
- Accusé de réception sous 48h ouvrées
- Traitement de votre réclamation sous 10 jours ouvrés
- Information régulière sur l'avancement de votre dossier
- Réponse claire et personnalisée

En cas d'insatisfaction persistante, vous pouvez saisir le médiateur de l'assurance dont les coordonnées figurent dans votre contrat.
        """
    },
    {
        "title": "Fiscalité des contrats santé",
        "category": "Réglementation",
        "content": """
Les contrats d'assurance santé responsables bénéficient d'avantages fiscaux :
- Pour les salariés : les cotisations versées par l'employeur sont exonérées de charges sociales dans certaines limites
- Pour les travailleurs non-salariés (TNS) : déductibilité des cotisations du revenu imposable dans le cadre de la loi Madelin

Conditions pour être considéré comme un contrat responsable :
- Prise en charge du ticket modérateur
- Respect des plafonds de remboursement pour les dépassements d'honoraires
- Respect des planchers et plafonds pour les équipements optiques
- Non prise en charge de certaines franchises médicales

Tous nos contrats sont "responsables" et conformes aux exigences réglementaires en vigueur.
        """
    },
    {
        "title": "Réforme 100% Santé",
        "category": "Réglementation",
        "content": """
La réforme 100% Santé garantit un accès à des soins de qualité sans reste à charge dans trois domaines :

1. Optique :
   - Montures respectant les normes européennes
   - Verres traitant l'ensemble des troubles visuels
   - Prix plafonné à 30€ pour la monture
   - Renouvellement tous les 2 ans (sauf exceptions)

2. Dentaire :
   - Couronnes et bridges en céramique monolithique ou céramo-métallique
   - Prothèses amovibles à base de résine
   - Tarifs plafonnés selon le type de prothèse
   - Garantie 5 ans pour les couronnes

3. Audiologie :
   - Appareils de tous types (contour d'oreille, intra-auriculaire)
   - 12 canaux de réglage et 3 options minimum
   - Prix plafonné à 950€ par oreille
   - Garantie 4 ans et prestations de suivi

Tous nos contrats intègrent le 100% Santé conformément à la réglementation.
        """
    },
    {
        "title": "Protection des données personnelles",
        "category": "Réglementation",
        "content": """
Conformément au Règlement Général sur la Protection des Données (RGPD), nous nous engageons à :
- Collecter uniquement les données nécessaires à la gestion de votre contrat
- Conserver vos données pendant la durée légale requise
- Ne pas transmettre vos données à des tiers non autorisés
- Assurer la sécurité et la confidentialité de vos informations

Vos droits concernant vos données personnelles :
- Droit d'accès : consulter les données vous concernant
- Droit de rectification : corriger les informations inexactes
- Droit à l'effacement : demander la suppression de vos données
- Droit à la limitation du traitement
- Droit à la portabilité : récupérer vos données dans un format structuré
- Droit d'opposition : vous opposer au traitement de vos données

Pour exercer ces droits, contactez notre Délégué à la Protection des Données à l'adresse dpo@assursante.example.
        """
    }
]

def create_qdrant_collection():
    """Crée une collection dans Qdrant pour stocker les vecteurs de la base de connaissances."""
    try:
        client = QdrantClient(host=VECTOR_DB_HOST, port=6333)
        
        # Vérification si la collection existe déjà
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if COLLECTION_NAME in collection_names:
            print(f"La collection '{COLLECTION_NAME}' existe déjà. Suppression et recréation...")
            client.delete_collection(collection_name=COLLECTION_NAME)
        
        # Création de la collection
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        
        print(f"✅ Collection '{COLLECTION_NAME}' créée avec succès.")
        return client
    
    except Exception as e:
        print(f"❌ Erreur lors de la création de la collection: {e}")
        return None

def vectorize_documents(model, documents):
    """Vectorise les documents de la base de connaissances."""
    print(f"Vectorisation de {len(documents)} documents...")
    
    # Préparation des textes à vectoriser
    texts = []
    for doc in documents:
        # Combinaison du titre et du contenu pour une meilleure représentation
        text = f"{doc['title']}. {doc['content']}"
        texts.append(text)
    
    # Vectorisation par lots pour éviter les problèmes de mémoire
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        batch_vectors = model.encode(batch)
        vectors.extend(batch_vectors)
        print(f"  Lot {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1} vectorisé.")
    
    return vectors

def insert_vectors_to_qdrant(client, documents, vectors):
    """Insère les vecteurs dans la collection Qdrant."""
    try:
        print("Insertion des vecteurs dans Qdrant...")
        
        # Préparation des points à insérer
        points = []
        for i, (doc, vector) in enumerate(zip(documents, vectors)):
            points.append(
                models.PointStruct(
                    id=i,
                    vector=vector.tolist(),
                    payload={
                        "title": doc["title"],
                        "category": doc["category"],
                        "content": doc["content"]
                    }
                )
            )
        
        # Insertion des points
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        print(f"✅ {len(points)} documents insérés dans Qdrant.")
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des vecteurs: {e}")
        return False

def test_vector_search(client, model, query="Comment obtenir un remboursement pour mes lunettes ?"):
    """Teste la recherche vectorielle avec une requête exemple."""
    try:
        print(f"\nTest de recherche avec la requête: '{query}'")
        
        # Vectorisation de la requête
        query_vector = model.encode(query).tolist()
        
        # Recherche des documents similaires
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3
        )
        
        print("\nRésultats de la recherche:")
        for i, result in enumerate(search_result):
            print(f"\n--- Résultat {i+1} (score: {result.score:.4f}) ---")
            print(f"Titre: {result.payload['title']}")
            print(f"Catégorie: {result.payload['category']}")
            print(f"Extrait: {result.payload['content'][:150]}...")
        
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors du test de recherche: {e}")
        return False

def save_knowledge_to_json(documents, filename='knowledge_base.json'):
    """Sauvegarde la base de connaissances dans un fichier JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Base de connaissances sauvegardée dans {filename}")

def main():
    """Fonction principale pour vectoriser la base de connaissances."""
    print("Initialisation de la base de connaissances vectorielle...")
    
    # Création de la collection Qdrant
    client = create_qdrant_collection()
    if not client:
        return
    
    # Chargement du modèle de vectorisation
    print(f"Chargement du modèle '{MODEL_NAME}'...")
    try:
        model = SentenceTransformer(MODEL_NAME)
        print(f"✅ Modèle chargé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        return
    
    # Vectorisation des documents
    vectors = vectorize_documents(model, KNOWLEDGE_BASE)
    
    # Insertion des vecteurs dans Qdrant
    success = insert_vectors_to_qdrant(client, KNOWLEDGE_BASE, vectors)
    if not success:
        return
    
    # Sauvegarde de la base de connaissances au format JSON
    save_knowledge_to_json(KNOWLEDGE_BASE)
    
    # Test de recherche vectorielle
    test_queries = [
        "Comment obtenir un remboursement pour mes lunettes ?",
        "Quels sont les délais de carence pour les soins dentaires ?",
        "Je souhaite résilier mon contrat, quelle est la procédure ?",
        "Quelles sont les garanties du niveau Premium ?"
    ]
    
    for query in test_queries:
        test_vector_search(client, model, query)

if __name__ == "__main__":
    main()
