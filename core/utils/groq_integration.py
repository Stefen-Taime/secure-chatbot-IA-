#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'intégration avec l'API Groq pour le POC de chatbot IA AssurSanté.
Ce module fournit les fonctions nécessaires pour interagir avec les modèles LLM de Groq.
"""

import os
import json
import requests
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv('../docker/.env')

# Configuration de l'API Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'your_groq_api_key_here')
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama3-70b-8192"  # Modèle par défaut

class GroqClient:
    """Client pour interagir avec l'API Groq."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise le client Groq.
        
        Args:
            api_key: Clé API Groq (utilise la variable d'environnement si non spécifiée)
            model: Modèle Groq à utiliser (utilise le modèle par défaut si non spécifié)
        """
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL
        
        if not self.api_key or self.api_key == 'your_groq_api_key_here':
            raise ValueError("Clé API Groq non configurée. Veuillez définir la variable d'environnement GROQ_API_KEY.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, 
                        messages: List[Dict[str, str]], 
                        temperature: float = 0.7, 
                        max_tokens: int = 1024,
                        stream: bool = False) -> Dict[str, Any]:
        """
        Envoie une requête de complétion de chat à l'API Groq.
        
        Args:
            messages: Liste des messages de la conversation
            temperature: Température pour le sampling (0.0 à 1.0)
            max_tokens: Nombre maximum de tokens à générer
            stream: Si True, retourne une réponse en streaming
            
        Returns:
            Réponse de l'API Groq
        """
        url = f"{GROQ_API_BASE}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            if stream:
                return self._process_stream(response)
            else:
                return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête à l'API Groq: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Détails de l'erreur: {e.response.text}")
            raise
    
    def _process_stream(self, response):
        """
        Traite une réponse en streaming de l'API Groq.
        
        Args:
            response: Réponse de l'API en streaming
            
        Returns:
            Générateur de chunks de réponse
        """
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Supprime le préfixe 'data: '
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError:
                        print(f"Erreur de décodage JSON: {data}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Obtient l'embedding d'un texte via l'API Groq.
        
        Args:
            text: Texte à encoder
            
        Returns:
            Vecteur d'embedding
        """
        url = f"{GROQ_API_BASE}/embeddings"
        
        payload = {
            "model": "embed-english-v3.0",  # Modèle d'embedding de Groq
            "input": text
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result["data"][0]["embedding"]
        
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête d'embedding à l'API Groq: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Détails de l'erreur: {e.response.text}")
            raise

# Système de prompts pour le contexte d'assurance santé
class InsurancePromptSystem:
    """Système de prompts spécifiques au contexte d'assurance santé."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        Retourne le prompt système de base pour le contexte d'assurance santé.
        
        Returns:
            Prompt système
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
    def format_client_context(client_data: Dict[str, Any]) -> str:
        """
        Formate les données client pour les inclure dans le contexte.
        
        Args:
            client_data: Données du client
            
        Returns:
            Contexte formaté
        """
        context = f"""
INFORMATIONS CLIENT:
Nom: {client_data.get('nom', 'Non disponible')} {client_data.get('prenom', 'Non disponible')}
ID Client: {client_data.get('id', 'Non disponible')}
Email: {client_data.get('email', 'Non disponible')}
Téléphone: {client_data.get('telephone', 'Non disponible')}
Numéro de sécurité sociale: {client_data.get('numero_securite_sociale', 'Non disponible')}

CONTRATS:
"""
        
        if 'contrats' in client_data and client_data['contrats']:
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
            context += "Aucun contrat trouvé pour ce client.\n"
        
        return context
    
    @staticmethod
    def format_claim_context(claim_data: Dict[str, Any]) -> str:
        """
        Formate les données de réclamation pour les inclure dans le contexte.
        
        Args:
            claim_data: Données de la réclamation
            
        Returns:
            Contexte formaté
        """
        context = f"""
RÉCLAMATION:
Numéro: {claim_data.get('numero_reclamation', 'Non disponible')}
Type: {claim_data.get('type_reclamation', 'Non disponible')}
Statut: {claim_data.get('statut', 'Non disponible')}
Date de création: {claim_data.get('date_reclamation', 'Non disponible')}
"""
        
        if claim_data.get('date_traitement'):
            context += f"Date de traitement: {claim_data.get('date_traitement')}\n"
        
        if claim_data.get('agent_traitement'):
            context += f"Agent en charge: {claim_data.get('agent_traitement')}\n"
        
        context += f"""
Description: {claim_data.get('description', 'Non disponible')}
"""
        
        if claim_data.get('montant_demande'):
            context += f"Montant demandé: {claim_data.get('montant_demande')}€\n"
        
        if claim_data.get('commentaires'):
            context += f"Commentaires: {claim_data.get('commentaires')}\n"
        
        return context
    
    @staticmethod
    def format_knowledge_context(knowledge_items: List[Dict[str, Any]]) -> str:
        """
        Formate les éléments de la base de connaissances pour les inclure dans le contexte.
        
        Args:
            knowledge_items: Éléments de la base de connaissances
            
        Returns:
            Contexte formaté
        """
        if not knowledge_items:
            return "Aucune information pertinente trouvée dans la base de connaissances."
        
        context = "INFORMATIONS PERTINENTES DE LA BASE DE CONNAISSANCES:\n\n"
        
        for i, item in enumerate(knowledge_items, 1):
            context += f"Document {i}: {item.get('title', 'Sans titre')}\n"
            context += f"Catégorie: {item.get('category', 'Non catégorisé')}\n"
            context += f"Contenu:\n{item.get('content', 'Contenu non disponible')}\n\n"
        
        return context

# Exemples de prompts spécifiques pour différents scénarios d'assurance
class InsurancePrompts:
    """Collection de prompts spécifiques pour différents scénarios d'assurance."""
    
    @staticmethod
    def remboursement_prompt() -> str:
        """Prompt pour les questions de remboursement."""
        return """Pour traiter une demande de remboursement, veuillez suivre ces étapes:

1. Vérifiez si les soins sont couverts par le contrat du client
2. Identifiez le niveau de garantie et le taux de remboursement applicable
3. Vérifiez si des justificatifs spécifiques sont nécessaires
4. Expliquez le délai de traitement standard
5. Précisez les modalités de transmission des justificatifs

Utilisez les informations du contrat du client pour personnaliser votre réponse."""
    
    @staticmethod
    def reclamation_prompt() -> str:
        """Prompt pour le traitement des réclamations."""
        return """Pour traiter une réclamation, veuillez suivre ces étapes:

1. Accusez réception de la réclamation avec empathie
2. Résumez la situation pour montrer votre compréhension
3. Vérifiez le statut actuel de la réclamation
4. Expliquez les prochaines étapes du traitement
5. Proposez un délai de résolution réaliste
6. Indiquez comment le client sera informé de l'avancement

Adaptez votre réponse en fonction du type de réclamation et de son statut actuel."""
    
    @staticmethod
    def contrat_prompt() -> str:
        """Prompt pour les questions sur les contrats."""
        return """Pour répondre aux questions sur les contrats, veuillez suivre ces étapes:

1. Identifiez le(s) contrat(s) actif(s) du client
2. Vérifiez les garanties spécifiques demandées
3. Expliquez clairement les couvertures et limitations
4. Précisez les délais de carence si applicables
5. Mentionnez les options ou garanties complémentaires pertinentes

Utilisez un langage clair et évitez le jargon technique sauf si nécessaire."""
    
    @staticmethod
    def resiliation_prompt() -> str:
        """Prompt pour les demandes de résiliation."""
        return """Pour traiter une demande de résiliation, veuillez suivre ces étapes:

1. Identifiez le motif de résiliation
2. Vérifiez si le client est dans son droit de résilier (Loi Hamon, échéance annuelle, etc.)
3. Expliquez la procédure à suivre et les documents nécessaires
4. Précisez les délais de traitement et la date effective de résiliation
5. Informez sur les éventuels remboursements de cotisations

Essayez de comprendre les raisons de la résiliation pour proposer éventuellement des alternatives adaptées."""

# Fonction utilitaire pour tester l'intégration avec Groq
def test_groq_integration():
    """
    Teste l'intégration avec l'API Groq.
    
    Returns:
        True si le test est réussi, False sinon
    """
    try:
        client = GroqClient()
        
        system_prompt = InsurancePromptSystem.get_system_prompt()
        user_prompt = "Comment fonctionne le remboursement des lunettes chez AssurSanté?"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"Test d'intégration avec Groq (modèle: {client.model})...")
        print(f"Requête: {user_prompt}")
        
        start_time = time.time()
        response = client.chat_completion(messages, temperature=0.7)
        end_time = time.time()
        
        print(f"\nRéponse reçue en {end_time - start_time:.2f} secondes:")
        print(response['choices'][0]['message']['content'])
        
        return True
    
    except Exception as e:
        print(f"Erreur lors du test d'intégration avec Groq: {e}")
        return False

if __name__ == "__main__":
    # Test de l'intégration avec Groq
    test_groq_integration()
