#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'implémentation du chaînage de prompts pour le POC de chatbot IA AssurSanté.
Ce module permet de décomposer des requêtes complexes en sous-tâches et de les traiter séquentiellement.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from .groq_integration import GroqClient
from .prompt_templates import PromptTemplates

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromptChaining:
    """
    Implémentation du pattern de chaînage de prompts pour le chatbot IA.
    Permet de décomposer des requêtes complexes en sous-tâches et de les traiter séquentiellement.
    """
    
    def __init__(self, groq_client: Optional[GroqClient] = None):
        """
        Initialise le système de chaînage de prompts.
        
        Args:
            groq_client: Client Groq pour les appels API
        """
        self.groq_client = groq_client or GroqClient()
        self.templates = PromptTemplates()
    
    def decompose_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Décompose une requête complexe en sous-tâches.
        
        Args:
            query: Requête utilisateur complexe
            
        Returns:
            Liste de sous-tâches à exécuter
        """
        # Prompt pour décomposer la requête
        decompose_prompt = """Vous êtes un assistant spécialisé dans l'analyse et la décomposition de requêtes complexes.
Votre tâche est de décomposer la requête utilisateur en sous-tâches logiques qui peuvent être traitées séquentiellement.

Pour chaque sous-tâche, identifiez :
1. Un titre court
2. Une description de ce qui doit être fait
3. Les dépendances (quelles sous-tâches doivent être complétées avant celle-ci)
4. Le type de sous-tâche (recherche, analyse, calcul, génération)

Formatez votre réponse en JSON selon ce schéma :
{
  "subtasks": [
    {
      "id": "1",
      "title": "Titre de la sous-tâche",
      "description": "Description détaillée",
      "dependencies": [],
      "type": "recherche"
    },
    {
      "id": "2",
      "title": "Titre de la sous-tâche",
      "description": "Description détaillée",
      "dependencies": ["1"],
      "type": "analyse"
    }
  ]
}

Requête utilisateur à décomposer : """
        
        # Appel à l'API Groq pour décomposer la requête
        messages = [
            {"role": "system", "content": decompose_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = self.groq_client.chat_completion(messages, temperature=0.3)
            content = response['choices'][0]['message']['content']
            
            # Extraction du JSON de la réponse
            try:
                # Tentative de parsing direct
                subtasks = json.loads(content)
                return subtasks.get('subtasks', [])
            except json.JSONDecodeError:
                # Si échec, tentative d'extraction du JSON de la réponse textuelle
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    try:
                        subtasks = json.loads(json_str)
                        return subtasks.get('subtasks', [])
                    except json.JSONDecodeError:
                        logger.error("Impossible d'extraire le JSON de la réponse")
                
                # Si tout échoue, retour d'une tâche unique
                return [{
                    "id": "1",
                    "title": "Traiter la requête complète",
                    "description": query,
                    "dependencies": [],
                    "type": "analyse"
                }]
        
        except Exception as e:
            logger.error(f"Erreur lors de la décomposition de la requête: {e}")
            # En cas d'erreur, retour d'une tâche unique
            return [{
                "id": "1",
                "title": "Traiter la requête complète",
                "description": query,
                "dependencies": [],
                "type": "analyse"
            }]
    
    def execute_subtask(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une sous-tâche spécifique.
        
        Args:
            subtask: Sous-tâche à exécuter
            context: Contexte d'exécution (résultats des sous-tâches précédentes, etc.)
            
        Returns:
            Résultat de l'exécution de la sous-tâche
        """
        task_type = subtask.get('type', '').lower()
        task_description = subtask.get('description', '')
        
        # Construction du prompt en fonction du type de tâche
        if task_type == 'recherche':
            prompt = f"""Vous êtes un assistant spécialisé dans la recherche d'informations dans le contexte d'assurance santé.
Votre tâche est de rechercher les informations pertinentes pour répondre à la demande suivante :

{task_description}

Utilisez uniquement les informations fournies dans le contexte. Si l'information n'est pas disponible, indiquez-le clairement.
Formatez votre réponse de manière concise et structurée."""
        
        elif task_type == 'analyse':
            prompt = f"""Vous êtes un assistant spécialisé dans l'analyse d'informations dans le contexte d'assurance santé.
Votre tâche est d'analyser les informations disponibles pour répondre à la demande suivante :

{task_description}

Basez votre analyse sur les informations du contexte et les résultats des sous-tâches précédentes.
Présentez votre analyse de manière structurée avec des conclusions claires."""
        
        elif task_type == 'calcul':
            prompt = f"""Vous êtes un assistant spécialisé dans les calculs liés à l'assurance santé.
Votre tâche est d'effectuer les calculs nécessaires pour répondre à la demande suivante :

{task_description}

Utilisez les informations du contexte et les résultats des sous-tâches précédentes.
Présentez vos calculs étape par étape et donnez un résultat final précis."""
        
        elif task_type == 'génération':
            prompt = f"""Vous êtes un assistant spécialisé dans la génération de contenu dans le contexte d'assurance santé.
Votre tâche est de générer le contenu demandé :

{task_description}

Basez votre génération sur les informations du contexte et les résultats des sous-tâches précédentes.
Le contenu doit être professionnel, précis et adapté au contexte d'assurance santé."""
        
        else:
            # Type de tâche non reconnu, utilisation d'un prompt générique
            prompt = f"""Vous êtes un assistant spécialisé dans l'assurance santé.
Votre tâche est de traiter la demande suivante :

{task_description}

Utilisez les informations disponibles dans le contexte pour fournir une réponse précise et complète."""
        
        # Construction du contexte pour l'API
        context_str = ""
        for key, value in context.items():
            if key != 'current_subtask':  # Exclusion de la sous-tâche courante
                context_str += f"\n--- {key} ---\n{value}\n"
        
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": prompt},
            {"role": "system", "content": f"CONTEXTE:\n{context_str}"},
            {"role": "user", "content": task_description}
        ]
        
        try:
            response = self.groq_client.chat_completion(messages, temperature=0.5)
            result = response['choices'][0]['message']['content']
            
            return {
                "subtask_id": subtask.get('id'),
                "title": subtask.get('title'),
                "result": result,
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la sous-tâche {subtask.get('id')}: {e}")
            
            return {
                "subtask_id": subtask.get('id'),
                "title": subtask.get('title'),
                "result": f"Erreur lors de l'exécution: {str(e)}",
                "status": "failed"
            }
    
    def execute_chain(self, query: str, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Exécute une chaîne complète de prompts pour une requête complexe.
        
        Args:
            query: Requête utilisateur complexe
            initial_context: Contexte initial (données client, etc.)
            
        Returns:
            Résultat final de l'exécution de la chaîne
        """
        # Initialisation du contexte
        context = initial_context or {}
        context['query'] = query
        
        # Décomposition de la requête en sous-tâches
        subtasks = self.decompose_query(query)
        logger.info(f"Requête décomposée en {len(subtasks)} sous-tâches")
        
        # Stockage des résultats des sous-tâches
        results = {}
        
        # Exécution des sous-tâches dans l'ordre des dépendances
        remaining_tasks = subtasks.copy()
        completed_task_ids = set()
        
        while remaining_tasks:
            # Recherche des tâches prêtes à être exécutées (toutes les dépendances sont satisfaites)
            ready_tasks = []
            for task in remaining_tasks:
                dependencies = set(task.get('dependencies', []))
                if dependencies.issubset(completed_task_ids):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Si aucune tâche n'est prête, il y a un problème de dépendances circulaires
                logger.error("Dépendances circulaires détectées, impossible de continuer")
                break
            
            # Exécution des tâches prêtes
            for task in ready_tasks:
                logger.info(f"Exécution de la sous-tâche {task.get('id')}: {task.get('title')}")
                
                # Mise à jour du contexte avec la sous-tâche courante
                context['current_subtask'] = task
                
                # Exécution de la sous-tâche
                result = self.execute_subtask(task, context)
                
                # Stockage du résultat
                task_id = task.get('id')
                results[task_id] = result
                
                # Mise à jour du contexte avec le résultat
                context[f"result_{task_id}"] = result.get('result', '')
                
                # Marquage de la tâche comme complétée
                completed_task_ids.add(task_id)
                remaining_tasks.remove(task)
        
        # Synthèse des résultats
        return self.synthesize_results(query, results, context)
    
    def synthesize_results(self, query: str, subtask_results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthétise les résultats des sous-tâches en une réponse finale.
        
        Args:
            query: Requête utilisateur originale
            subtask_results: Résultats des sous-tâches
            context: Contexte d'exécution
            
        Returns:
            Réponse finale synthétisée
        """
        # Construction du prompt de synthèse
        synthesis_prompt = """Vous êtes un assistant spécialisé dans la synthèse d'informations dans le contexte d'assurance santé.
Votre tâche est de synthétiser les résultats des différentes sous-tâches pour produire une réponse cohérente et complète à la requête originale de l'utilisateur.

La réponse doit être :
1. Complète et précise, couvrant tous les aspects de la requête
2. Structurée de manière logique et facile à comprendre
3. Professionnelle et adaptée au contexte d'assurance santé
4. Concise mais sans omettre d'informations importantes

Requête originale de l'utilisateur : """
        
        # Construction du contexte des résultats
        results_context = ""
        for task_id, result in subtask_results.items():
            results_context += f"\n--- Résultat de la sous-tâche {task_id}: {result.get('title')} ---\n"
            results_context += result.get('result', 'Aucun résultat disponible')
            results_context += "\n"
        
        # Appel à l'API Groq pour la synthèse
        messages = [
            {"role": "system", "content": synthesis_prompt},
            {"role": "system", "content": f"RÉSULTATS DES SOUS-TÂCHES:\n{results_context}"},
            {"role": "user", "content": query}
        ]
        
        try:
            response = self.groq_client.chat_completion(messages, temperature=0.7)
            synthesis = response['choices'][0]['message']['content']
            
            return {
                "query": query,
                "synthesis": synthesis,
                "subtask_results": subtask_results,
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse des résultats: {e}")
            
            # En cas d'erreur, retour des résultats bruts
            return {
                "query": query,
                "synthesis": "Erreur lors de la synthèse des résultats. Voici les résultats bruts des sous-tâches.",
                "subtask_results": subtask_results,
                "status": "partial"
            }

# Exemple d'utilisation du chaînage de prompts
def example_usage():
    """Exemple d'utilisation du chaînage de prompts."""
    # Création du système de chaînage
    chaining = PromptChaining()
    
    # Exemple de requête complexe
    query = "Je souhaite comprendre comment fonctionne le remboursement des lunettes avec mon contrat Premium, et savoir si je peux ajouter mon enfant qui vient de naître à mon contrat famille."
    
    # Contexte initial
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
        }
    }
    
    # Exécution de la chaîne
    result = chaining.execute_chain(query, context)
    
    # Affichage du résultat
    print("Requête originale:")
    print(query)
    print("\nSynthèse:")
    print(result.get('synthesis', 'Aucune synthèse disponible'))

if __name__ == "__main__":
    example_usage()
