#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de prompts spécifiques pour le chatbot IA AssurSanté.
Ce module contient les templates de prompts pour différents scénarios d'assurance santé.
"""

from typing import Dict, List, Any

class PromptTemplates:
    """Collection de templates de prompts pour le chatbot IA AssurSanté."""
    
    @staticmethod
    def get_base_system_prompt() -> str:
        """
        Retourne le prompt système de base pour le chatbot.
        
        Returns:
            Prompt système de base
        """
        return """Vous êtes un assistant IA spécialisé dans l'assurance santé, travaillant pour AssurSanté.
Votre rôle est d'aider les agents du service client à répondre aux questions des assurés.
Vous devez être précis, professionnel et empathique dans vos réponses.

Directives importantes:
1. Basez vos réponses uniquement sur les informations fournies dans le contexte.
2. Si vous ne connaissez pas la réponse, indiquez-le clairement et suggérez de contacter un conseiller.
3. Pour les questions médicales spécifiques, précisez que seul un professionnel de santé peut donner un avis médical.
4. Respectez la confidentialité des données personnelles des assurés.
5. Utilisez un langage clair et accessible, évitez le jargon technique sauf si nécessaire.
6. Structurez vos réponses de manière logique avec des paragraphes distincts pour faciliter la lecture.
7. Lorsque vous citez des montants de remboursement ou des garanties, précisez toujours le niveau de contrat concerné.

Vous avez accès aux informations sur les contrats, les garanties, les procédures de remboursement et les démarches administratives d'AssurSanté."""
    
    @staticmethod
    def get_intent_specific_prompts() -> Dict[str, str]:
        """
        Retourne les prompts spécifiques à chaque intention.
        
        Returns:
            Dictionnaire des prompts par intention
        """
        return {
            "remboursement": """Pour traiter une demande de remboursement, veuillez suivre ces étapes:

1. Vérifiez si les soins sont couverts par le contrat du client
2. Identifiez le niveau de garantie et le taux de remboursement applicable
3. Vérifiez si des justificatifs spécifiques sont nécessaires
4. Expliquez le délai de traitement standard
5. Précisez les modalités de transmission des justificatifs

Utilisez les informations du contrat du client pour personnaliser votre réponse.""",
            
            "reclamation": """Pour traiter une réclamation, veuillez suivre ces étapes:

1. Accusez réception de la réclamation avec empathie
2. Résumez la situation pour montrer votre compréhension
3. Vérifiez le statut actuel de la réclamation
4. Expliquez les prochaines étapes du traitement
5. Proposez un délai de résolution réaliste
6. Indiquez comment le client sera informé de l'avancement

Adaptez votre réponse en fonction du type de réclamation et de son statut actuel.""",
            
            "contrat": """Pour répondre aux questions sur les contrats, veuillez suivre ces étapes:

1. Identifiez le(s) contrat(s) actif(s) du client
2. Vérifiez les garanties spécifiques demandées
3. Expliquez clairement les couvertures et limitations
4. Précisez les délais de carence si applicables
5. Mentionnez les options ou garanties complémentaires pertinentes

Utilisez un langage clair et évitez le jargon technique sauf si nécessaire.""",
            
            "resiliation": """Pour traiter une demande de résiliation, veuillez suivre ces étapes:

1. Identifiez le motif de résiliation
2. Vérifiez si le client est dans son droit de résilier (Loi Hamon, échéance annuelle, etc.)
3. Expliquez la procédure à suivre et les documents nécessaires
4. Précisez les délais de traitement et la date effective de résiliation
5. Informez sur les éventuels remboursements de cotisations

Essayez de comprendre les raisons de la résiliation pour proposer éventuellement des alternatives adaptées.""",
            
            "modification": """Pour traiter une demande de modification de contrat, veuillez suivre ces étapes:

1. Identifiez le type de modification souhaitée
2. Vérifiez si la modification est possible selon les termes du contrat
3. Expliquez la procédure à suivre et les documents nécessaires
4. Précisez les délais de traitement et la date effective de la modification
5. Informez sur les éventuels impacts sur la cotisation

Assurez-vous que le client comprend bien les conséquences de la modification demandée.""",
            
            "prise_en_charge": """Pour traiter une demande de prise en charge, veuillez suivre ces étapes:

1. Identifiez le type de soins concerné
2. Vérifiez si les soins sont couverts par le contrat du client
3. Expliquez la procédure de demande de prise en charge
4. Précisez les délais de traitement et les documents nécessaires
5. Informez sur les modalités de transmission de l'attestation de prise en charge

Pour les hospitalisations programmées, rappelez que la demande doit être effectuée au moins 5 jours avant la date prévue."""
        }
    
    @staticmethod
    def format_context_data(client_data: Dict[str, Any] = None, 
                           claim_data: Dict[str, Any] = None,
                           knowledge_items: List[Dict[str, Any]] = None) -> str:
        """
        Formate les données de contexte pour le prompt.
        
        Args:
            client_data: Données du client
            claim_data: Données de la réclamation
            knowledge_items: Éléments de la base de connaissances
            
        Returns:
            Contexte formaté
        """
        context = ""
        
        # Ajout du contexte client si disponible
        if client_data:
            context += """
INFORMATIONS CLIENT:
"""
            context += f"Nom: {client_data.get('nom', 'Non disponible')} {client_data.get('prenom', 'Non disponible')}\n"
            context += f"ID Client: {client_data.get('id', 'Non disponible')}\n"
            context += f"Email: {client_data.get('email', 'Non disponible')}\n"
            context += f"Téléphone: {client_data.get('telephone', 'Non disponible')}\n"
            context += f"Numéro de sécurité sociale: {client_data.get('numero_securite_sociale', 'Non disponible')}\n"
            
            # Ajout des contrats si disponibles
            if 'contrats' in client_data and client_data['contrats']:
                context += "\nCONTRATS:\n"
                for i, contrat in enumerate(client_data['contrats'], 1):
                    context += f"""
Contrat {i}:
- Numéro: {contrat.get('numero_contrat', 'Non disponible')}
- Type: {contrat.get('type_contrat', 'Non disponible')}
- Niveau: {contrat.get('niveau_couverture', 'Non disponible')}
- Statut: {contrat.get('statut', 'Non disponible')}
- Date début: {contrat.get('date_debut', 'Non disponible')}
- Date fin: {contrat.get('date_fin', 'Non disponible')}
- Cotisation mensuelle: {contrat.get('montant_cotisation', 'Non disponible')}€
"""
            else:
                context += "\nAucun contrat trouvé pour ce client.\n"
        
        # Ajout du contexte de réclamation si disponible
        if claim_data:
            context += """
RÉCLAMATION:
"""
            context += f"Numéro: {claim_data.get('numero_reclamation', 'Non disponible')}\n"
            context += f"Type: {claim_data.get('type_reclamation', 'Non disponible')}\n"
            context += f"Statut: {claim_data.get('statut', 'Non disponible')}\n"
            context += f"Date de création: {claim_data.get('date_reclamation', 'Non disponible')}\n"
            
            if claim_data.get('date_traitement'):
                context += f"Date de traitement: {claim_data.get('date_traitement')}\n"
            
            if claim_data.get('agent_traitement'):
                context += f"Agent en charge: {claim_data.get('agent_traitement')}\n"
            
            context += f"\nDescription: {claim_data.get('description', 'Non disponible')}\n"
            
            if claim_data.get('montant_demande'):
                context += f"Montant demandé: {claim_data.get('montant_demande')}€\n"
            
            if claim_data.get('commentaires'):
                context += f"Commentaires: {claim_data.get('commentaires')}\n"
        
        # Ajout du contexte de connaissances si disponible
        if knowledge_items:
            context += """
INFORMATIONS PERTINENTES DE LA BASE DE CONNAISSANCES:
"""
            for i, item in enumerate(knowledge_items, 1):
                context += f"\nDocument {i}: {item.get('title', 'Sans titre')}\n"
                context += f"Catégorie: {item.get('category', 'Non catégorisé')}\n"
                context += f"Contenu:\n{item.get('content', 'Contenu non disponible')}\n"
        
        return context
    
    @staticmethod
    def get_few_shot_examples() -> List[Dict[str, str]]:
        """
        Retourne des exemples few-shot pour améliorer les réponses du modèle.
        
        Returns:
            Liste d'exemples few-shot
        """
        return [
            {
                "user": "Je n'ai pas reçu le remboursement de ma consultation chez le cardiologue du mois dernier.",
                "assistant": """Je comprends votre préoccupation concernant le remboursement de votre consultation chez le cardiologue.

D'après les informations de votre contrat Premium, les consultations chez un spécialiste sont remboursées à 100% du tarif de convention plus les dépassements d'honoraires jusqu'à 300% du tarif de convention.

Le délai standard de remboursement est de 3 à 5 jours ouvrés après réception des justificatifs complets. Plusieurs raisons peuvent expliquer ce retard :
1. Les justificatifs n'ont pas encore été reçus ou sont incomplets
2. La Sécurité Sociale n'a pas encore traité votre demande
3. Un problème technique a pu retarder le traitement

Je vous recommande de vérifier si :
- Vous avez bien transmis le décompte de la Sécurité Sociale
- La facture acquittée du médecin a été jointe à votre demande

Si tous les documents ont été envoyés, je peux faire une demande de vérification auprès de notre service de gestion des remboursements. Souhaitez-vous que je procède à cette vérification ?"""
            },
            {
                "user": "Je souhaite ajouter mon nouveau-né à mon contrat famille.",
                "assistant": """Félicitations pour la naissance de votre enfant ! Je vais vous guider pour l'ajout de votre nouveau-né à votre contrat Santé Famille.

D'après votre contrat actuel, vous bénéficiez du niveau Confort qui couvre l'ensemble de votre famille. L'ajout d'un nouveau bénéficiaire est possible à tout moment suite à un changement de situation familiale comme une naissance.

Voici la procédure à suivre :
1. Nous aurons besoin d'une copie de l'acte de naissance ou du livret de famille mis à jour
2. Le formulaire d'ajout de bénéficiaire (disponible sur votre espace client ou que je peux vous envoyer)
3. La copie de l'attestation de droits de la Sécurité Sociale mentionnant l'enfant

Ces documents peuvent être transmis :
- Via votre espace client en ligne
- Par email à gestion@assursante.example
- Par courrier à notre service gestion

L'ajout prendra effet dès réception des documents complets, sans délai de carence pour votre nouveau-né. Votre cotisation sera ajustée à partir du mois suivant l'ajout.

Souhaitez-vous que je vous envoie le formulaire d'ajout de bénéficiaire ?"""
            },
            {
                "user": "Quelles sont les démarches pour obtenir une prise en charge pour mon opération programmée ?",
                "assistant": """Pour obtenir une prise en charge pour votre opération programmée, voici les démarches à suivre :

Selon votre contrat Premium, vous bénéficiez d'une prise en charge à 100% des frais de séjour et du forfait hospitalier, ainsi que d'une chambre particulière jusqu'à 90€ par jour.

Voici la procédure pour obtenir votre prise en charge :
1. Contactez notre service de prise en charge au moins 5 jours avant la date d'hospitalisation prévue
2. Préparez les informations suivantes :
   - Votre numéro d'adhérent (indiqué sur votre carte de tiers payant)
   - La date d'entrée prévue
   - Le nom et l'adresse de l'établissement hospitalier
   - Le service d'admission
   - La nature de l'hospitalisation (médicale, chirurgicale, ambulatoire)

Vous pouvez faire cette demande :
- Par téléphone au 01 XX XX XX XX (service disponible du lundi au vendredi de 9h à 18h)
- Via votre espace client en ligne, rubrique "Demande de prise en charge"
- Par email à priseencharge@assursante.example

Une attestation de prise en charge sera envoyée directement à l'établissement hospitalier, avec copie par email pour vous. Vous n'aurez ainsi pas à avancer les frais couverts par votre contrat.

Avez-vous déjà la date de votre opération et les coordonnées de l'établissement ?"""
            }
        ]

# Exemples d'utilisation des templates
def example_usage():
    """Exemple d'utilisation des templates de prompts."""
    templates = PromptTemplates()
    
    # Exemple de prompt système de base
    system_prompt = templates.get_base_system_prompt()
    print("Prompt système de base:")
    print(system_prompt)
    print("\n" + "-"*80 + "\n")
    
    # Exemple de prompt spécifique à une intention
    intent_prompts = templates.get_intent_specific_prompts()
    print("Prompt spécifique à l'intention 'remboursement':")
    print(intent_prompts["remboursement"])
    print("\n" + "-"*80 + "\n")
    
    # Exemple de formatage de contexte
    client_data = {
        "id": 42,
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@example.com",
        "telephone": "0123456789",
        "numero_securite_sociale": "175042789456712",
        "contrats": [
            {
                "numero_contrat": "CONT-2023-042",
                "type_contrat": "Santé Famille",
                "niveau_couverture": "Premium",
                "statut": "Actif",
                "date_debut": "2023-01-01",
                "date_fin": "2025-12-31",
                "montant_cotisation": 120.50
            }
        ]
    }
    
    context = templates.format_context_data(client_data=client_data)
    print("Exemple de contexte formaté:")
    print(context)

if __name__ == "__main__":
    example_usage()
