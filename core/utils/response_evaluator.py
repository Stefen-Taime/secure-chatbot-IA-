#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'implémentation de l'évaluateur-optimiseur pour le POC de chatbot IA AssurSanté.
Ce module permet d'évaluer et d'optimiser la qualité des réponses générées.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from .groq_integration import GroqClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResponseEvaluator:
    """
    Implémentation de l'évaluateur-optimiseur pour le chatbot IA.
    Permet d'évaluer et d'optimiser la qualité des réponses générées.
    """
    
    def __init__(self, groq_client: Optional[GroqClient] = None):
        """
        Initialise l'évaluateur-optimiseur.
        
        Args:
            groq_client: Client Groq pour les appels API
        """
        self.groq_client = groq_client or GroqClient()
        
        # Critères d'évaluation
        self.evaluation_criteria = {
            "relevance": {
                "description": "Pertinence par rapport à la requête",
                "weight": 0.25
            },
            "accuracy": {
                "description": "Exactitude factuelle",
                "weight": 0.25
            },
            "completeness": {
                "description": "Complétude de la réponse",
                "weight": 0.20
            },
            "clarity": {
                "description": "Clarté et structure",
                "weight": 0.15
            },
            "tone": {
                "description": "Ton et professionnalisme",
                "weight": 0.15
            }
        }
    
    def set_evaluation_criteria(self, criteria: Dict[str, Dict[str, Any]]) -> None:
        """
        Définit les critères d'évaluation.
        
        Args:
            criteria: Dictionnaire des critères d'évaluation
        """
        self.evaluation_criteria = criteria
    
    def evaluate_relevance(self, query: str, response: str) -> Dict[str, Any]:
        """
        Évalue la pertinence de la réponse par rapport à la requête.
        
        Args:
            query: Requête utilisateur
            response: Réponse générée
            
        Returns:
            Évaluation de la pertinence
        """
        prompt = """Vous êtes un expert en évaluation de la qualité des réponses dans le domaine de l'assurance santé. Votre tâche est d'évaluer la pertinence de la réponse par rapport à la requête utilisateur.

Une réponse est considérée comme pertinente si elle :
1. Répond directement à la question ou au besoin exprimé
2. Aborde tous les aspects de la requête
3. Ne contient pas d'informations hors sujet ou non sollicitées
4. Est adaptée au contexte spécifique de la demande
5. Fournit le niveau de détail approprié

Requête utilisateur : {query}

Réponse à évaluer : {response}

Évaluez la pertinence de cette réponse sur une échelle de 0 à 10, où :
- 0-2 : Réponse non pertinente (hors sujet ou sans rapport avec la requête)
- 3-5 : Réponse partiellement pertinente (aborde certains aspects mais en ignore d'autres)
- 6-8 : Réponse pertinente (répond à la requête de manière satisfaisante)
- 9-10 : Réponse très pertinente (répond parfaitement à tous les aspects de la requête)

Fournissez votre évaluation au format JSON :
{{
  "score": 0-10,
  "normalized_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "strengths": ["Points forts de la réponse"],
  "weaknesses": ["Points faibles de la réponse"],
  "improvement_suggestions": ["Suggestions d'amélioration"]
}}
"""
        
        prompt = prompt.format(query=query, response=response)
        return self._evaluate_criterion(prompt, "relevance")
    
    def evaluate_accuracy(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Évalue l'exactitude factuelle de la réponse.
        
        Args:
            response: Réponse générée
            context: Contexte de la conversation
            
        Returns:
            Évaluation de l'exactitude
        """
        # Construction du contexte formaté
        context_str = ""
        for key, value in context.items():
            if isinstance(value, dict) or isinstance(value, list):
                context_str += f"\n--- {key} ---\n{json.dumps(value, ensure_ascii=False, indent=2)}\n"
            else:
                context_str += f"\n--- {key} ---\n{value}\n"
        
        prompt = """Vous êtes un expert en évaluation de la qualité des réponses dans le domaine de l'assurance santé. Votre tâche est d'évaluer l'exactitude factuelle de la réponse par rapport au contexte fourni.

Une réponse est considérée comme exacte si elle :
1. Contient des informations factuellement correctes
2. Est cohérente avec les informations du contexte
3. Ne contient pas d'erreurs ou d'imprécisions
4. Ne fait pas d'affirmations non étayées par le contexte
5. Distingue clairement les faits des opinions ou suppositions

Contexte : {context}

Réponse à évaluer : {response}

Évaluez l'exactitude de cette réponse sur une échelle de 0 à 10, où :
- 0-2 : Réponse très inexacte (contient des erreurs graves ou des contradictions)
- 3-5 : Réponse partiellement exacte (contient quelques erreurs ou imprécisions)
- 6-8 : Réponse exacte (informations correctes avec quelques nuances manquantes)
- 9-10 : Réponse très exacte (parfaitement conforme aux faits et au contexte)

Fournissez votre évaluation au format JSON :
{{
  "score": 0-10,
  "normalized_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "strengths": ["Points forts de la réponse"],
  "weaknesses": ["Points faibles de la réponse"],
  "improvement_suggestions": ["Suggestions d'amélioration"]
}}
"""
        
        prompt = prompt.format(context=context_str, response=response)
        return self._evaluate_criterion(prompt, "accuracy")
    
    def evaluate_completeness(self, query: str, response: str) -> Dict[str, Any]:
        """
        Évalue la complétude de la réponse.
        
        Args:
            query: Requête utilisateur
            response: Réponse générée
            
        Returns:
            Évaluation de la complétude
        """
        prompt = """Vous êtes un expert en évaluation de la qualité des réponses dans le domaine de l'assurance santé. Votre tâche est d'évaluer la complétude de la réponse par rapport à la requête utilisateur.

Une réponse est considérée comme complète si elle :
1. Couvre tous les aspects de la requête
2. Fournit toutes les informations nécessaires
3. Inclut les détails pratiques pertinents (procédures, délais, etc.)
4. Anticipe les questions de suivi évidentes
5. Ne laisse pas d'ambiguïtés ou de zones d'ombre importantes

Requête utilisateur : {query}

Réponse à évaluer : {response}

Évaluez la complétude de cette réponse sur une échelle de 0 à 10, où :
- 0-2 : Réponse très incomplète (omet des aspects essentiels)
- 3-5 : Réponse partiellement complète (aborde les points principaux mais manque de détails)
- 6-8 : Réponse complète (couvre tous les aspects avec un niveau de détail satisfaisant)
- 9-10 : Réponse très complète (couvre tous les aspects avec un excellent niveau de détail)

Fournissez votre évaluation au format JSON :
{{
  "score": 0-10,
  "normalized_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "strengths": ["Points forts de la réponse"],
  "weaknesses": ["Points faibles de la réponse"],
  "improvement_suggestions": ["Suggestions d'amélioration"]
}}
"""
        
        prompt = prompt.format(query=query, response=response)
        return self._evaluate_criterion(prompt, "completeness")
    
    def evaluate_clarity(self, response: str) -> Dict[str, Any]:
        """
        Évalue la clarté et la structure de la réponse.
        
        Args:
            response: Réponse générée
            
        Returns:
            Évaluation de la clarté
        """
        prompt = """Vous êtes un expert en évaluation de la qualité des réponses dans le domaine de l'assurance santé. Votre tâche est d'évaluer la clarté et la structure de la réponse.

Une réponse est considérée comme claire et bien structurée si elle :
1. Est facile à comprendre, même pour un non-spécialiste
2. Utilise un langage précis et accessible
3. Est organisée de manière logique avec une progression cohérente
4. Utilise des paragraphes et des sections appropriés
5. Évite le jargon technique inutile ou l'explique lorsqu'il est nécessaire

Réponse à évaluer : {response}

Évaluez la clarté et la structure de cette réponse sur une échelle de 0 à 10, où :
- 0-2 : Réponse très confuse (difficile à comprendre, mal organisée)
- 3-5 : Réponse moyennement claire (compréhensible mais avec des passages confus)
- 6-8 : Réponse claire (bien organisée et facile à comprendre)
- 9-10 : Réponse très claire (parfaitement structurée et limpide)

Fournissez votre évaluation au format JSON :
{{
  "score": 0-10,
  "normalized_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "strengths": ["Points forts de la réponse"],
  "weaknesses": ["Points faibles de la réponse"],
  "improvement_suggestions": ["Suggestions d'amélioration"]
}}
"""
        
        prompt = prompt.format(response=response)
        return self._evaluate_criterion(prompt, "clarity")
    
    def evaluate_tone(self, response: str) -> Dict[str, Any]:
        """
        Évalue le ton et le professionnalisme de la réponse.
        
        Args:
            response: Réponse générée
            
        Returns:
            Évaluation du ton
        """
        prompt = """Vous êtes un expert en évaluation de la qualité des réponses dans le domaine de l'assurance santé. Votre tâche est d'évaluer le ton et le professionnalisme de la réponse.

Une réponse est considérée comme ayant un ton approprié et professionnel si elle :
1. Est respectueuse et courtoise
2. Fait preuve d'empathie lorsque nécessaire
3. Maintient un niveau de formalité adapté au contexte
4. Évite les formulations condescendantes ou trop familières
5. Reflète les valeurs d'une entreprise d'assurance santé professionnelle

Réponse à évaluer : {response}

Évaluez le ton et le professionnalisme de cette réponse sur une échelle de 0 à 10, où :
- 0-2 : Ton très inapproprié (impoli, trop familier ou insensible)
- 3-5 : Ton moyennement approprié (correct mais manquant d'empathie ou de professionnalisme)
- 6-8 : Ton approprié (professionnel et adapté au contexte)
- 9-10 : Ton parfaitement approprié (excellent équilibre entre professionnalisme et empathie)

Fournissez votre évaluation au format JSON :
{{
  "score": 0-10,
  "normalized_score": 0.0-1.0,
  "reasoning": "Explication détaillée de votre évaluation",
  "strengths": ["Points forts de la réponse"],
  "weaknesses": ["Points faibles de la réponse"],
  "improvement_suggestions": ["Suggestions d'amélioration"]
}}
"""
        
        prompt = prompt.format(response=response)
        return self._evaluate_criterion(prompt, "tone")
    
    def _evaluate_criterion(self, prompt: str, criterion: str) -> Dict[str, Any]:
        """
        Évalue un critère spécifique.
        
        Args:
            prompt: Prompt d'évaluation
            criterion: Critère à évaluer
            
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
                        logger.error(f"Impossible d'extraire le JSON de l'évaluation pour le critère {criterion}")
                        evaluation = {
                            "score": 5,
                            "normalized_score": 0.5,
                            "reasoning": f"Erreur d'analyse de la réponse d'évaluation pour {criterion}",
                            "strengths": [],
                            "weaknesses": ["Format de réponse invalide"],
                            "improvement_suggestions": ["Vérifier le format de la réponse"]
                        }
                else:
                    evaluation = {
                        "score": 5,
                        "normalized_score": 0.5,
                        "reasoning": f"Erreur d'analyse de la réponse d'évaluation pour {criterion}",
                        "strengths": [],
                        "weaknesses": ["Format de réponse invalide"],
                        "improvement_suggestions": ["Vérifier le format de la réponse"]
                    }
            
            # Ajout du critère
            evaluation["criterion"] = criterion
            
            # Calcul du score normalisé si non présent
            if "normalized_score" not in evaluation and "score" in evaluation:
                evaluation["normalized_score"] = evaluation["score"] / 10.0
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du critère {criterion}: {e}")
            
            return {
                "criterion": criterion,
                "score": 5,
                "normalized_score": 0.5,
                "reasoning": f"Erreur technique lors de l'évaluation: {str(e)}",
                "strengths": [],
                "weaknesses": ["Erreur technique"],
                "improvement_suggestions": ["Réessayer l'évaluation"]
            }
    
    def evaluate_response(self, query: str, response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Évalue une réponse complète selon tous les critères.
        
        Args:
            query: Requête utilisateur
            response: Réponse générée
            context: Contexte de la conversation
            
        Returns:
            Résultat complet de l'évaluation
        """
        context = context or {}
        results = {}
        
        # Évaluation de chaque critère
        results['relevance'] = self.evaluate_relevance(query, response)
        results['accuracy'] = self.evaluate_accuracy(response, context)
        results['completeness'] = self.evaluate_completeness(query, response)
        results['clarity'] = self.evaluate_clarity(response)
        results['tone'] = self.evaluate_tone(response)
        
        # Calcul du score global (moyenne pondérée)
        total_weight = 0
        weighted_score = 0
        
        for criterion, result in results.items():
            weight = self.evaluation_criteria.get(criterion, {}).get("weight", 0.2)
            score = result.get("normalized_score", 0.5)
            
            weighted_score += score * weight
            total_weight += weight
        
        global_score = weighted_score / total_weight if total_weight > 0 else 0.5
        
        # Compilation des forces, faiblesses et suggestions
        strengths = []
        weaknesses = []
        improvement_suggestions = []
        
        for criterion, result in results.items():
            strengths.extend(result.get("strengths", []))
            weaknesses.extend(result.get("weaknesses", []))
            improvement_suggestions.extend(result.get("improvement_suggestions", []))
        
        return {
            "global_score": global_score,
            "criterion_results": results,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": improvement_suggestions
        }
    
    def optimize_response(self, query: str, response: str, evaluation: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """
        Optimise une réponse en fonction de son évaluation.
        
        Args:
            query: Requête utilisateur
            response: Réponse originale
            evaluation: Résultat de l'évaluation
            context: Contexte de la conversation
            
        Returns:
            Réponse optimisée
        """
        # Construction des instructions d'optimisation
        instructions = "Votre tâche est d'optimiser la réponse suivante en fonction de l'évaluation fournie.\n\n"
        
        # Ajout du score global
        global_score = evaluation.get("global_score", 0.5)
        instructions += f"Score global de la réponse : {global_score:.2f}/1.0\n\n"
        
        # Ajout des scores par critère
        instructions += "Scores par critère :\n"
        for criterion, result in evaluation.get("criterion_results", {}).items():
            score = result.get("normalized_score", 0.5)
            instructions += f"- {criterion.capitalize()}: {score:.2f}/1.0\n"
        
        instructions += "\n"
        
        # Ajout des faiblesses identifiées
        if evaluation.get("weaknesses"):
            instructions += "Faiblesses à corriger :\n"
            for weakness in evaluation.get("weaknesses"):
                instructions += f"- {weakness}\n"
            instructions += "\n"
        
        # Ajout des suggestions d'amélioration
        if evaluation.get("improvement_suggestions"):
            instructions += "Suggestions d'amélioration :\n"
            for suggestion in evaluation.get("improvement_suggestions"):
                instructions += f"- {suggestion}\n"
            instructions += "\n"
        
        # Ajout des forces à conserver
        if evaluation.get("strengths"):
            instructions += "Forces à conserver :\n"
            for strength in evaluation.get("strengths"):
                instructions += f"- {strength}\n"
            instructions += "\n"
        
        # Construction du prompt complet
        prompt = f"""Vous êtes un expert en optimisation de réponses dans le domaine de l'assurance santé. {instructions}

Requête originale de l'utilisateur :
{query}

Réponse à optimiser :
{response}

Veuillez fournir une version optimisée de la réponse qui :
1. Corrige les faiblesses identifiées
2. Intègre les suggestions d'amélioration
3. Conserve les forces de la réponse originale
4. Reste fidèle à l'intention de la réponse originale
5. Est professionnelle, précise et adaptée au contexte d'assurance santé

Réponse optimisée :
"""
        
        # Ajout du contexte si disponible
        if context:
            context_str = "\nContexte disponible :\n"
            for key, value in context.items():
                if isinstance(value, dict) or isinstance(value, list):
                    context_str += f"\n--- {key} ---\n{json.dumps(value, ensure_ascii=False, indent=2)}\n"
                else:
                    context_str += f"\n--- {key} ---\n{value}\n"
            
            prompt = prompt.replace("Requête originale de l'utilisateur :", f"Requête originale de l'utilisateur :\n{query}\n{context_str}")
        
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        try:
            api_response = self.groq_client.chat_completion(messages, temperature=0.3)
            optimized_response = api_response['choices'][0]['message']['content']
            
            return optimized_response
        
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation de la réponse: {e}")
            
            # En cas d'erreur, retour de la réponse originale
            return response

# Exemple d'utilisation de l'évaluateur-optimiseur
def example_usage():
    """Exemple d'utilisation de l'évaluateur-optimiseur."""
    # Création de l'évaluateur
    evaluator = ResponseEvaluator()
    
    # Exemple de requête et réponse
    query = "Je souhaite savoir comment ajouter mon nouveau-né à mon contrat famille et quels documents je dois fournir."
    
    response = """Vous pouvez ajouter votre nouveau-né à votre contrat famille. Envoyez-nous l'acte de naissance et nous nous occuperons du reste. La modification prendra effet immédiatement."""
    
    # Contexte
    context = {
        "client": {
            "nom": "Dupont",
            "prenom": "Jean",
            "contrats": [
                {
                    "type": "Santé Famille",
                    "niveau": "Premium",
                    "statut": "Actif"
                }
            ]
        },
        "knowledge": {
            "ajout_beneficiaire": "Pour ajouter un bénéficiaire, les documents requis sont : acte de naissance ou livret de famille, formulaire d'ajout de bénéficiaire, attestation de droits de la Sécurité Sociale. L'ajout prend effet dès réception des documents complets, sans délai de carence pour les nouveau-nés."
        }
    }
    
    # Évaluation de la réponse
    print("Évaluation de la réponse...")
    evaluation = evaluator.evaluate_response(query, response, context)
    
    # Affichage du résultat
    print(f"Score global : {evaluation.get('global_score'):.2f}")
    
    print("\nFaiblesses identifiées :")
    for weakness in evaluation.get('weaknesses', []):
        print(f"- {weakness}")
    
    # Optimisation de la réponse
    print("\nOptimisation de la réponse...")
    optimized_response = evaluator.optimize_response(query, response, evaluation, context)
    
    print("\nRéponse optimisée :")
    print(optimized_response)

if __name__ == "__main__":
    example_usage()
