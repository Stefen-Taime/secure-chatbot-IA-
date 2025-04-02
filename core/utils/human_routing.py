#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'implémentation du mécanisme de routage vers des spécialistes humains pour le POC de chatbot IA AssurSanté.
Ce module permet de détecter quand une requête doit être transmise à un agent humain.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from .groq_integration import GroqClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HumanRoutingSystem:
    """
    Implémentation du mécanisme de routage vers des spécialistes humains pour le chatbot IA.
    Permet de détecter quand une requête doit être transmise à un agent humain et de gérer cette transition.
    """
    
    def __init__(self, groq_client: Optional[GroqClient] = None):
        """
        Initialise le système de routage vers des spécialistes humains.
        
        Args:
            groq_client: Client Groq pour les appels API
        """
        self.groq_client = groq_client or GroqClient()
        
        # Configuration des seuils de routage
        self.routing_thresholds = {
            "complexity": 0.7,  # Seuil de complexité pour le routage
            "sensitivity": 0.8,  # Seuil de sensibilité pour le routage
            "urgency": 0.8,      # Seuil d'urgence pour le routage
            "escalation": 0.7    # Seuil d'escalation pour le routage
        }
        
        # Configuration des spécialistes disponibles
        self.specialists = {
            "remboursement": {
                "name": "Service Remboursements",
                "description": "Spécialiste des remboursements et prises en charge",
                "availability": "Lundi au vendredi, 9h-18h"
            },
            "contrat": {
                "name": "Service Gestion des contrats",
                "description": "Spécialiste des modifications et résiliations de contrats",
                "availability": "Lundi au vendredi, 9h-17h"
            },
            "reclamation": {
                "name": "Service Réclamations",
                "description": "Spécialiste du traitement des réclamations",
                "availability": "Lundi au vendredi, 9h-16h"
            },
            "medical": {
                "name": "Service Médical",
                "description": "Conseiller médical pour les questions de santé",
                "availability": "Lundi au vendredi, 10h-16h"
            },
            "urgence": {
                "name": "Service Urgences",
                "description": "Traitement prioritaire des demandes urgentes",
                "availability": "Lundi au dimanche, 8h-20h"
            }
        }
    
    def set_routing_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Définit les seuils de routage.
        
        Args:
            thresholds: Dictionnaire des seuils de routage
        """
        self.routing_thresholds = thresholds
    
    def set_specialists(self, specialists: Dict[str, Dict[str, str]]) -> None:
        """
        Définit les spécialistes disponibles.
        
        Args:
            specialists: Dictionnaire des spécialistes disponibles
        """
        self.specialists = specialists
    
    def evaluate_complexity(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Évalue la complexité d'une requête utilisateur.
        
        Args:
            query: Requête utilisateur
            conversation_history: Historique de la conversation
            
        Returns:
            Évaluation de la complexité
        """
        # Construction du prompt
        prompt = """Vous êtes un expert en analyse de requêtes dans le domaine de l'assurance santé. Votre tâche est d'évaluer la complexité de la requête utilisateur.

Une requête est considérée comme complexe si elle :
1. Implique plusieurs sujets ou questions interconnectés
2. Nécessite une connaissance approfondie de réglementations spécifiques
3. Concerne des cas particuliers ou des exceptions aux règles standard
4. Requiert l'analyse de plusieurs documents ou contrats
5. Implique des calculs complexes ou des simulations

Évaluez la complexité de la requête suivante sur une échelle de 0 à 1, où :
- 0-0.3 : Requête simple (information factuelle, procédure standard)
- 0.3-0.6 : Requête modérément complexe (plusieurs étapes, quelques nuances)
- 0.6-0.8 : Requête complexe (multiples aspects, connaissances spécialisées)
- 0.8-1.0 : Requête très complexe (cas exceptionnels, multiples interdépendances)

Requête utilisateur : """
        
        # Ajout de l'historique de conversation si disponible
        if conversation_history:
            history_str = "\n\nHistorique de conversation :\n"
            for message in conversation_history[-5:]:  # Limité aux 5 derniers messages
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                history_str += f"{role}: {content}\n\n"
            
            prompt += query + history_str
        else:
            prompt += query
        
        prompt += """

Fournissez votre analyse au format JSON :
{
  "complexity_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "complex_aspects": ["Liste des aspects complexes identifiés"]
}
"""
        
        return self._evaluate_dimension(prompt, "complexity")
    
    def evaluate_sensitivity(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Évalue la sensibilité d'une requête utilisateur.
        
        Args:
            query: Requête utilisateur
            context: Contexte de la conversation
            
        Returns:
            Évaluation de la sensibilité
        """
        # Construction du prompt
        prompt = """Vous êtes un expert en analyse de requêtes dans le domaine de l'assurance santé. Votre tâche est d'évaluer la sensibilité de la requête utilisateur.

Une requête est considérée comme sensible si elle :
1. Concerne des informations médicales confidentielles
2. Implique des situations personnelles délicates (décès, maladie grave, etc.)
3. Touche à des aspects financiers importants (refus de remboursement, litiges)
4. Mentionne une insatisfaction ou une réclamation explicite
5. Fait référence à des procédures juridiques ou contentieuses

Évaluez la sensibilité de la requête suivante sur une échelle de 0 à 1, où :
- 0-0.3 : Requête peu sensible (information générale, procédure standard)
- 0.3-0.6 : Requête modérément sensible (information personnelle non critique)
- 0.6-0.8 : Requête sensible (information médicale, insatisfaction)
- 0.8-1.0 : Requête très sensible (situation critique, litige, détresse)

Requête utilisateur : """
        
        # Ajout du contexte si disponible
        if context:
            context_str = "\n\nContexte :\n"
            for key, value in context.items():
                if isinstance(value, dict) or isinstance(value, list):
                    context_str += f"\n--- {key} ---\n{json.dumps(value, ensure_ascii=False, indent=2)}\n"
                else:
                    context_str += f"\n--- {key} ---\n{value}\n"
            
            prompt += query + context_str
        else:
            prompt += query
        
        prompt += """

Fournissez votre analyse au format JSON :
{
  "sensitivity_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "sensitive_aspects": ["Liste des aspects sensibles identifiés"]
}
"""
        
        return self._evaluate_dimension(prompt, "sensitivity")
    
    def evaluate_urgency(self, query: str) -> Dict[str, Any]:
        """
        Évalue l'urgence d'une requête utilisateur.
        
        Args:
            query: Requête utilisateur
            
        Returns:
            Évaluation de l'urgence
        """
        # Construction du prompt
        prompt = """Vous êtes un expert en analyse de requêtes dans le domaine de l'assurance santé. Votre tâche est d'évaluer l'urgence de la requête utilisateur.

Une requête est considérée comme urgente si elle :
1. Mentionne explicitement une urgence ou une échéance imminente
2. Concerne une hospitalisation en cours ou imminente
3. Implique une situation médicale critique nécessitant une action rapide
4. Fait référence à un blocage administratif empêchant des soins
5. Mentionne un préjudice financier imminent (rejet de paiement, découvert)

Évaluez l'urgence de la requête suivante sur une échelle de 0 à 1, où :
- 0-0.3 : Requête non urgente (information générale, délai standard acceptable)
- 0.3-0.6 : Requête peu urgente (action nécessaire dans les prochains jours)
- 0.6-0.8 : Requête urgente (action nécessaire dans les 24-48h)
- 0.8-1.0 : Requête très urgente (action nécessaire immédiatement ou dans les heures qui suivent)

Requête utilisateur : """
        
        prompt += query
        
        prompt += """

Fournissez votre analyse au format JSON :
{
  "urgency_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "urgency_indicators": ["Liste des indicateurs d'urgence identifiés"]
}
"""
        
        return self._evaluate_dimension(prompt, "urgency")
    
    def evaluate_escalation_need(self, query: str, ai_response: str = None) -> Dict[str, Any]:
        """
        Évalue si une requête nécessite une escalade vers un spécialiste humain.
        
        Args:
            query: Requête utilisateur
            ai_response: Réponse générée par l'IA (si disponible)
            
        Returns:
            Évaluation du besoin d'escalade
        """
        # Construction du prompt
        prompt = """Vous êtes un expert en analyse de requêtes dans le domaine de l'assurance santé. Votre tâche est d'évaluer si la requête utilisateur nécessite une escalade vers un spécialiste humain.

Une requête nécessite généralement une escalade si :
1. Elle demande explicitement à parler à un humain ou un responsable
2. Elle exprime une insatisfaction face à des réponses automatisées précédentes
3. Elle concerne une situation exceptionnelle non couverte par les procédures standard
4. Elle implique une décision qui nécessite un jugement humain ou une approbation
5. Elle fait référence à un problème récurrent non résolu

Requête utilisateur : """
        
        # Ajout de la réponse IA si disponible
        if ai_response:
            prompt += query + "\n\nRéponse générée par l'IA :\n" + ai_response
        else:
            prompt += query
        
        prompt += """

Évaluez le besoin d'escalade sur une échelle de 0 à 1, où :
- 0-0.3 : Escalade non nécessaire (l'IA peut gérer la requête)
- 0.3-0.6 : Escalade potentiellement utile mais non critique
- 0.6-0.8 : Escalade recommandée (valeur ajoutée significative d'un humain)
- 0.8-1.0 : Escalade nécessaire (requête impossible à traiter correctement par l'IA)

Fournissez votre analyse au format JSON :
{
  "escalation_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "escalation_indicators": ["Liste des indicateurs d'escalade identifiés"]
}
"""
        
        return self._evaluate_dimension(prompt, "escalation")
    
    def _evaluate_dimension(self, prompt: str, dimension: str) -> Dict[str, Any]:
        """
        Évalue une dimension spécifique (complexité, sensibilité, urgence, escalade).
        
        Args:
            prompt: Prompt d'évaluation
            dimension: Dimension à évaluer
            
        Returns:
            Résultat de l'évaluation
        """
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        try:
            api_response = self.groq_client.chat_completion(messages, temperature=0.1)
            content = api_response['choices'][0]['message']['content']
            
            # Extraction du JSON de la réponse
            try:
                # Tentative de parsing direct
                evaluation = json.loads(content)
            except json.JSONDecodeError:
                # Si échec, tentative d'extraction du JSON de la réponse textuelle
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    try:
                        evaluation = json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.error(f"Impossible d'extraire le JSON de l'évaluation pour la dimension {dimension}")
                        evaluation = {
                            f"{dimension}_score": 0.5,
                            "reasoning": f"Erreur d'analyse de la réponse d'évaluation pour {dimension}",
                            f"{dimension}_indicators": ["Format de réponse invalide"]
                        }
                else:
                    evaluation = {
                        f"{dimension}_score": 0.5,
                        "reasoning": f"Erreur d'analyse de la réponse d'évaluation pour {dimension}",
                        f"{dimension}_indicators": ["Format de réponse invalide"]
                    }
            
            # Ajout de la dimension
            evaluation["dimension"] = dimension
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la dimension {dimension}: {e}")
            
            return {
                "dimension": dimension,
                f"{dimension}_score": 0.5,
                "reasoning": f"Erreur technique lors de l'évaluation: {str(e)}",
                f"{dimension}_indicators": ["Erreur technique"]
            }
    
    def determine_specialist(self, query: str, evaluations: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Détermine le spécialiste le plus approprié pour traiter une requête.
        
        Args:
            query: Requête utilisateur
            evaluations: Évaluations précédentes (si disponibles)
            
        Returns:
            Spécialiste recommandé
        """
        # Construction du prompt
        prompt = """Vous êtes un expert en routage de requêtes dans le domaine de l'assurance santé. Votre tâche est de déterminer le service spécialiste le plus approprié pour traiter la requête utilisateur.

Les services spécialistes disponibles sont :
1. Service Remboursements : pour les questions de remboursements et prises en charge
2. Service Gestion des contrats : pour les modifications et résiliations de contrats
3. Service Réclamations : pour le traitement des réclamations et litiges
4. Service Médical : pour les questions nécessitant une expertise médicale
5. Service Urgences : pour les demandes urgentes nécessitant un traitement prioritaire

Requête utilisateur : """
        
        prompt += query
        
        # Ajout des évaluations si disponibles
        if evaluations:
            eval_str = "\n\nÉvaluations précédentes :\n"
            for dim, eval_data in evaluations.items():
                score_key = f"{dim}_score"
                if score_key in eval_data:
                    eval_str += f"- {dim.capitalize()}: {eval_data[score_key]:.2f}\n"
                    if "reasoning" in eval_data:
                        eval_str += f"  Raison: {eval_data['reasoning']}\n"
            
            prompt += eval_str
        
        prompt += """

Déterminez le service spécialiste le plus approprié et fournissez votre analyse au format JSON :
{
  "recommended_specialist": "remboursement|contrat|reclamation|medical|urgence",
  "confidence": 0.0-1.0,
  "reasoning": "Explication détaillée de votre recommandation",
  "alternative_specialist": "remboursement|contrat|reclamation|medical|urgence"
}
"""
        
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        try:
            api_response = self.groq_client.chat_completion(messages, temperature=0.2)
            content = api_response['choices'][0]['message']['content']
            
            # Extraction du JSON de la réponse
            try:
                # Tentative de parsing direct
                specialist_data = json.loads(content)
            except json.JSONDecodeError:
                # Si échec, tentative d'extraction du JSON de la réponse textuelle
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    try:
                        specialist_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.error("Impossible d'extraire le JSON de la recommandation de spécialiste")
                        specialist_data = {
                            "recommended_specialist": "remboursement",
                            "confidence": 0.5,
                            "reasoning": "Erreur d'analyse de la réponse, spécialiste par défaut sélectionné",
                            "alternative_specialist": "contrat"
                        }
                else:
                    specialist_data = {
                        "recommended_specialist": "remboursement",
                        "confidence": 0.5,
                        "reasoning": "Erreur d'analyse de la réponse, spécialiste par défaut sélectionné",
                        "alternative_specialist": "contrat"
                    }
            
            # Ajout des informations du spécialiste
            specialist_id = specialist_data.get("recommended_specialist", "remboursement")
            if specialist_id in self.specialists:
                specialist_data["specialist_info"] = self.specialists[specialist_id]
            else:
                specialist_data["specialist_info"] = self.specialists["remboursement"]
                specialist_data["recommended_specialist"] = "remboursement"
            
            return specialist_data
        
        except Exception as e:
            logger.error(f"Erreur lors de la détermination du spécialiste: {e}")
            
            return {
                "recommended_specialist": "remboursement",
                "confidence": 0.5,
                "reasoning": f"Erreur technique lors de la détermination du spécialiste: {str(e)}",
                "alternative_specialist": "contrat",
                "specialist_info": self.specialists["remboursement"]
            }
    
    def evaluate_routing_need(self, query: str, ai_response: str = None, context: Dict[str, Any] = None, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Évalue si une requête doit être routée vers un spécialiste humain.
        
        Args:
            query: Requête utilisateur
            ai_response: Réponse générée par l'IA (si disponible)
            context: Contexte de la conversation
            conversation_history: Historique de la conversation
            
        Returns:
            Résultat complet de l'évaluation de routage
        """
        # Évaluation des différentes dimensions
        evaluations = {}
        
        # Évaluation de la complexité
        complexity_eval = self.evaluate_complexity(query, conversation_history)
        evaluations["complexity"] = complexity_eval
        
        # Évaluation de la sensibilité
        sensitivity_eval = self.evaluate_sensitivity(query, context)
        evaluations["sensitivity"] = sensitivity_eval
        
        # Évaluation de l'urgence
        urgency_eval = self.evaluate_urgency(query)
        evaluations["urgency"] = urgency_eval
        
        # Évaluation du besoin d'escalade
        if ai_response:
            escalation_eval = self.evaluate_escalation_need(query, ai_response)
            evaluations["escalation"] = escalation_eval
        
        # Détermination du spécialiste recommandé
        specialist_recommendation = self.determine_specialist(query, evaluations)
        
        # Décision de routage
        routing_needed = False
        routing_reasons = []
        
        # Vérification des seuils pour chaque dimension
        complexity_score = complexity_eval.get("complexity_score", 0)
        if complexity_score >= self.routing_thresholds.get("complexity", 0.7):
            routing_needed = True
            routing_reasons.append(f"Complexité élevée ({complexity_score:.2f})")
        
        sensitivity_score = sensitivity_eval.get("sensitivity_score", 0)
        if sensitivity_score >= self.routing_thresholds.get("sensitivity", 0.8):
            routing_needed = True
            routing_reasons.append(f"Sensibilité élevée ({sensitivity_score:.2f})")
        
        urgency_score = urgency_eval.get("urgency_score", 0)
        if urgency_score >= self.routing_thresholds.get("urgency", 0.8):
            routing_needed = True
            routing_reasons.append(f"Urgence élevée ({urgency_score:.2f})")
        
        if "escalation" in evaluations:
            escalation_score = evaluations["escalation"].get("escalation_score", 0)
            if escalation_score >= self.routing_thresholds.get("escalation", 0.7):
                routing_needed = True
                routing_reasons.append(f"Besoin d'escalade élevé ({escalation_score:.2f})")
        
        # Construction du résultat final
        result = {
            "routing_needed": routing_needed,
            "routing_reasons": routing_reasons,
            "specialist_recommendation": specialist_recommendation,
            "evaluations": evaluations
        }
        
        return result
    
    def generate_handover_message(self, query: str, routing_evaluation: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """
        Génère un message de transfert vers un spécialiste humain.
        
        Args:
            query: Requête utilisateur
            routing_evaluation: Évaluation du besoin de routage
            context: Contexte de la conversation
            
        Returns:
            Message de transfert
        """
        # Extraction des informations du spécialiste
        specialist_recommendation = routing_evaluation.get("specialist_recommendation", {})
        specialist_id = specialist_recommendation.get("recommended_specialist", "remboursement")
        specialist_info = specialist_recommendation.get("specialist_info", self.specialists.get(specialist_id, {}))
        
        specialist_name = specialist_info.get("name", "Service client")
        specialist_availability = specialist_info.get("availability", "Horaires standard")
        
        # Construction du prompt
        prompt = f"""Vous êtes un assistant IA spécialisé dans l'assurance santé. Votre tâche est de générer un message de transfert vers un spécialiste humain.

Le message doit :
1. Informer l'utilisateur que sa demande va être transmise à un spécialiste humain
2. Expliquer brièvement pourquoi (complexité, sensibilité, urgence, etc.)
3. Préciser quel service va traiter sa demande et les horaires de disponibilité
4. Rassurer l'utilisateur sur la prise en charge de sa demande
5. Être empathique, professionnel et rassurant

Informations sur le spécialiste :
- Service : {specialist_name}
- Disponibilité : {specialist_availability}

Raisons du transfert :
"""
        
        # Ajout des raisons du transfert
        for reason in routing_evaluation.get("routing_reasons", ["Demande nécessitant une expertise humaine"]):
            prompt += f"- {reason}\n"
        
        prompt += f"\nRequête utilisateur : {query}\n"
        
        # Ajout du contexte si disponible
        if context:
            context_str = "\nContexte :\n"
            for key, value in context.items():
                if isinstance(value, dict) or isinstance(value, list):
                    context_str += f"\n--- {key} ---\n{json.dumps(value, ensure_ascii=False, indent=2)}\n"
                else:
                    context_str += f"\n--- {key} ---\n{value}\n"
            
            prompt += context_str
        
        prompt += "\nVeuillez générer un message de transfert approprié :"
        
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        try:
            api_response = self.groq_client.chat_completion(messages, temperature=0.7)
            handover_message = api_response['choices'][0]['message']['content']
            
            return handover_message
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du message de transfert: {e}")
            
            # Message de transfert par défaut en cas d'erreur
            return f"""Bonjour,

Je comprends que votre demande nécessite l'expertise d'un de nos spécialistes. Je vais transférer votre requête au {specialist_name}, qui pourra vous apporter une réponse personnalisée.

Ce service est disponible {specialist_availability}.

Un conseiller vous contactera dans les meilleurs délais. Merci de votre patience et de votre compréhension.

Cordialement,
Votre assistant AssurSanté"""

# Exemple d'utilisation du système de routage
def example_usage():
    """Exemple d'utilisation du système de routage vers des spécialistes humains."""
    # Création du système de routage
    routing = HumanRoutingSystem()
    
    # Exemple de requête complexe
    query = "Je suis très inquiet car ma fille de 5 ans doit être hospitalisée demain pour une opération et je viens de recevoir un refus de prise en charge. Mon employeur a changé de mutuelle il y a 3 semaines et je ne sais pas si mes droits sont bien transférés. J'ai besoin d'une solution urgente car je ne peux pas avancer les frais qui s'élèvent à plus de 4000€."
    
    # Réponse IA
    ai_response = """Je comprends votre inquiétude concernant la prise en charge de l'hospitalisation de votre fille.

D'après les informations dont je dispose, lors d'un changement de mutuelle par votre employeur, il y a normalement une continuité de couverture sans délai de carence. Cependant, il peut y avoir un délai administratif dans la mise à jour de vos droits.

Je vous recommande de contacter notre service de prise en charge hospitalière qui pourra traiter votre demande en priorité. Vous pouvez les joindre au 01 XX XX XX XX."""
    
    # Contexte
    context = {
        "client": {
            "nom": "Martin",
            "prenom": "Pierre",
            "contrats": [
                {
                    "type": "Santé Famille",
                    "niveau": "Confort",
                    "statut": "En cours de transfert"
                }
            ]
        }
    }
    
    # Évaluation du besoin de routage
    print("Évaluation du besoin de routage...")
    routing_evaluation = routing.evaluate_routing_need(query, ai_response, context)
    
    # Affichage du résultat
    print(f"Routage nécessaire : {routing_evaluation.get('routing_needed')}")
    if routing_evaluation.get('routing_needed'):
        print("\nRaisons du routage :")
        for reason in routing_evaluation.get('routing_reasons', []):
            print(f"- {reason}")
        
        specialist = routing_evaluation.get('specialist_recommendation', {})
        print(f"\nSpécialiste recommandé : {specialist.get('recommended_specialist')}")
        print(f"Confiance : {specialist.get('confidence', 0):.2f}")
        
        # Génération du message de transfert
        print("\nGénération du message de transfert...")
        handover_message = routing.generate_handover_message(query, routing_evaluation, context)
        
        print("\nMessage de transfert :")
        print(handover_message)

if __name__ == "__main__":
    example_usage()
