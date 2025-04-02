#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'intégration du chatbot IA avec l'API Groq pour AssurSanté.
Ce module implémente les prompts spécifiques et les workflows de conversation.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from .groq_integration import GroqClient, InsurancePromptSystem, InsurancePrompts

# Chargement des variables d'environnement
load_dotenv('../docker/.env')

class ChatbotOrchestrator:
    """
    Orchestrateur du chatbot IA pour AssurSanté.
    Gère les flux de conversation et l'intégration avec les différentes API.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None, groq_model: Optional[str] = None):
        """
        Initialise l'orchestrateur du chatbot.
        
        Args:
            groq_api_key: Clé API Groq (utilise la variable d'environnement si non spécifiée)
            groq_model: Modèle Groq à utiliser (utilise le modèle par défaut si non spécifié)
        """
        self.groq_client = GroqClient(api_key=groq_api_key, model=groq_model)
        self.conversation_history = []
        self.current_client = None
        self.current_claim = None
        self.knowledge_context = []
    
    def set_client_context(self, client_data: Dict[str, Any]) -> None:
        """
        Définit le contexte client pour la conversation.
        
        Args:
            client_data: Données du client
        """
        self.current_client = client_data
    
    def set_claim_context(self, claim_data: Dict[str, Any]) -> None:
        """
        Définit le contexte de réclamation pour la conversation.
        
        Args:
            claim_data: Données de la réclamation
        """
        self.current_claim = claim_data
    
    def set_knowledge_context(self, knowledge_items: List[Dict[str, Any]]) -> None:
        """
        Définit le contexte de connaissances pour la conversation.
        
        Args:
            knowledge_items: Éléments de la base de connaissances
        """
        self.knowledge_context = knowledge_items
    
    def build_context_prompt(self) -> str:
        """
        Construit le prompt de contexte complet pour la conversation.
        
        Returns:
            Prompt de contexte
        """
        context = ""
        
        # Ajout du contexte client si disponible
        if self.current_client:
            context += InsurancePromptSystem.format_client_context(self.current_client)
        
        # Ajout du contexte de réclamation si disponible
        if self.current_claim:
            context += InsurancePromptSystem.format_claim_context(self.current_claim)
        
        # Ajout du contexte de connaissances si disponible
        if self.knowledge_context:
            context += InsurancePromptSystem.format_knowledge_context(self.knowledge_context)
        
        return context
    
    def detect_intent(self, user_message: str) -> Tuple[str, float]:
        """
        Détecte l'intention de l'utilisateur à partir de son message.
        
        Args:
            user_message: Message de l'utilisateur
            
        Returns:
            Tuple contenant l'intention détectée et le score de confiance
        """
        # Liste des intentions possibles avec leurs mots-clés associés
        intents = {
            "remboursement": ["remboursement", "rembourser", "remboursé", "prise en charge", "frais", "dépense", "facture"],
            "reclamation": ["réclamation", "plainte", "problème", "erreur", "insatisfaction", "contester"],
            "contrat": ["contrat", "garantie", "couverture", "niveau", "option", "formule", "souscription"],
            "resiliation": ["résiliation", "résilier", "annuler", "annulation", "mettre fin", "arrêter"]
        }
        
        # Calcul du score pour chaque intention
        scores = {}
        user_message_lower = user_message.lower()
        
        for intent, keywords in intents.items():
            score = 0
            for keyword in keywords:
                if keyword in user_message_lower:
                    score += 1
            
            scores[intent] = score / len(keywords) if score > 0 else 0
        
        # Sélection de l'intention avec le score le plus élevé
        max_intent = max(scores.items(), key=lambda x: x[1])
        
        # Si aucune intention n'est détectée avec un score suffisant, on utilise l'intention par défaut
        if max_intent[1] < 0.2:
            return "general", 0.0
        
        return max_intent
    
    def get_intent_prompt(self, intent: str) -> str:
        """
        Récupère le prompt spécifique à l'intention détectée.
        
        Args:
            intent: Intention détectée
            
        Returns:
            Prompt spécifique à l'intention
        """
        intent_prompts = {
            "remboursement": InsurancePrompts.remboursement_prompt(),
            "reclamation": InsurancePrompts.reclamation_prompt(),
            "contrat": InsurancePrompts.contrat_prompt(),
            "resiliation": InsurancePrompts.resiliation_prompt(),
            "general": ""  # Pas de prompt spécifique pour l'intention générale
        }
        
        return intent_prompts.get(intent, "")
    
    def process_message(self, user_message: str, temperature: float = 0.7) -> str:
        """
        Traite un message utilisateur et génère une réponse.
        
        Args:
            user_message: Message de l'utilisateur
            temperature: Température pour le sampling (0.0 à 1.0)
            
        Returns:
            Réponse générée
        """
        # Détection de l'intention
        intent, confidence = self.detect_intent(user_message)
        
        # Construction du prompt système
        system_prompt = InsurancePromptSystem.get_system_prompt()
        
        # Ajout du prompt spécifique à l'intention si la confiance est suffisante
        intent_prompt = self.get_intent_prompt(intent)
        if intent_prompt:
            system_prompt += f"\n\n{intent_prompt}"
        
        # Construction du contexte
        context_prompt = self.build_context_prompt()
        
        # Ajout du message utilisateur à l'historique
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Construction des messages pour l'API Groq
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Ajout du contexte comme message système supplémentaire si disponible
        if context_prompt:
            messages.append({"role": "system", "content": f"CONTEXTE:\n{context_prompt}"})
        
        # Ajout de l'historique de conversation (limité aux 10 derniers messages)
        messages.extend(self.conversation_history[-10:])
        
        # Appel à l'API Groq
        response = self.groq_client.chat_completion(messages, temperature=temperature)
        
        # Extraction de la réponse
        assistant_message = response['choices'][0]['message']['content']
        
        # Ajout de la réponse à l'historique
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def process_message_stream(self, user_message: str, temperature: float = 0.7):
        """
        Traite un message utilisateur et génère une réponse en streaming.
        
        Args:
            user_message: Message de l'utilisateur
            temperature: Température pour le sampling (0.0 à 1.0)
            
        Returns:
            Générateur de chunks de réponse
        """
        # Détection de l'intention
        intent, confidence = self.detect_intent(user_message)
        
        # Construction du prompt système
        system_prompt = InsurancePromptSystem.get_system_prompt()
        
        # Ajout du prompt spécifique à l'intention si la confiance est suffisante
        intent_prompt = self.get_intent_prompt(intent)
        if intent_prompt:
            system_prompt += f"\n\n{intent_prompt}"
        
        # Construction du contexte
        context_prompt = self.build_context_prompt()
        
        # Ajout du message utilisateur à l'historique
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Construction des messages pour l'API Groq
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Ajout du contexte comme message système supplémentaire si disponible
        if context_prompt:
            messages.append({"role": "system", "content": f"CONTEXTE:\n{context_prompt}"})
        
        # Ajout de l'historique de conversation (limité aux 10 derniers messages)
        messages.extend(self.conversation_history[-10:])
        
        # Appel à l'API Groq en mode streaming
        response_stream = self.groq_client.chat_completion(
            messages, temperature=temperature, stream=True
        )
        
        # Traitement du stream et construction de la réponse complète
        full_response = ""
        
        for chunk in response_stream:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta and delta['content']:
                    content = delta['content']
                    full_response += content
                    yield content
        
        # Ajout de la réponse complète à l'historique
        self.conversation_history.append({"role": "assistant", "content": full_response})
    
    def clear_conversation_history(self) -> None:
        """Efface l'historique de conversation."""
        self.conversation_history = []
    
    def save_conversation(self, filename: str) -> bool:
        """
        Sauvegarde l'historique de conversation dans un fichier JSON.
        
        Args:
            filename: Nom du fichier de sauvegarde
            
        Returns:
            True si la sauvegarde est réussie, False sinon
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la conversation: {e}")
            return False
    
    def load_conversation(self, filename: str) -> bool:
        """
        Charge l'historique de conversation depuis un fichier JSON.
        
        Args:
            filename: Nom du fichier à charger
            
        Returns:
            True si le chargement est réussi, False sinon
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
            return True
        except Exception as e:
            print(f"Erreur lors du chargement de la conversation: {e}")
            return False

# Fonction utilitaire pour tester l'orchestrateur du chatbot
def test_chatbot_orchestrator():
    """
    Teste l'orchestrateur du chatbot avec un exemple de conversation.
    
    Returns:
        True si le test est réussi, False sinon
    """
    try:
        # Création de l'orchestrateur
        orchestrator = ChatbotOrchestrator()
        
        # Exemple de données client
        client_data = {
            "id": 42,
            "nom": "Dupont",
            "prenom": "Jean",
            "email": "jean.dupont@example.com",
            "telephone": "0123456789",
            "numero_securite_sociale": "175042789456712",
            "contrats": [
                {
                    "id": 123,
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
        
        # Exemple de réclamation
        claim_data = {
            "id": 789,
            "numero_reclamation": "REC-2024-123",
            "type_reclamation": "Remboursement",
            "statut": "En cours",
            "date_reclamation": "2024-03-15",
            "description": "Je n'ai toujours pas reçu le remboursement de ma consultation chez le spécialiste du 01/03/2024.",
            "montant_demande": 75.00
        }
        
        # Exemple d'éléments de la base de connaissances
        knowledge_items = [
            {
                "title": "Remboursement des consultations médicales",
                "category": "Remboursements",
                "content": "Les consultations médicales sont remboursées selon les conditions suivantes:\n- Médecin généraliste conventionné secteur 1: remboursement à 100% du tarif de convention\n- Médecin spécialiste conventionné secteur 2: remboursement à 100% du tarif de convention + dépassements selon niveau de garantie"
            }
        ]
        
        # Configuration du contexte
        orchestrator.set_client_context(client_data)
        orchestrator.set_claim_context(claim_data)
        orchestrator.set_knowledge_context(knowledge_items)
        
        # Test de traitement de message
        print("Test de l'orchestrateur du chatbot...")
        
        user_message = "Pouvez-vous me dire où en est ma demande de remboursement pour ma consultation chez le spécialiste ?"
        print(f"Message utilisateur: {user_message}")
        
        response = orchestrator.process_message(user_message, temperature=0.7)
        print(f"\nRéponse du chatbot:\n{response}")
        
        return True
    
    except Exception as e:
        print(f"Erreur lors du test de l'orchestrateur du chatbot: {e}")
        return False

if __name__ == "__main__":
    # Test de l'orchestrateur du chatbot
    test_chatbot_orchestrator()
