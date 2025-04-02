#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'implémentation du système de gating pour le POC de chatbot IA AssurSanté.
Ce module permet de vérifier la conformité des réponses avant leur envoi à l'utilisateur.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from .groq_integration import GroqClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GatingSystem:
    """
    Implémentation du pattern de gating pour le chatbot IA.
    Permet de vérifier la conformité des réponses avant leur envoi à l'utilisateur.
    """
    
    def __init__(self, groq_client: Optional[GroqClient] = None):
        """
        Initialise le système de gating.
        
        Args:
            groq_client: Client Groq pour les appels API
        """
        self.groq_client = groq_client or GroqClient()
        
        # Règles de conformité par défaut
        self.compliance_rules = {
            "medical_advice": {
                "description": "Vérification des conseils médicaux",
                "enabled": True,
                "severity": "high"
            },
            "personal_data": {
                "description": "Protection des données personnelles",
                "enabled": True,
                "severity": "high"
            },
            "legal_compliance": {
                "description": "Conformité légale et réglementaire",
                "enabled": True,
                "severity": "high"
            },
            "tone_politeness": {
                "description": "Ton et politesse",
                "enabled": True,
                "severity": "medium"
            },
            "factual_accuracy": {
                "description": "Exactitude factuelle",
                "enabled": True,
                "severity": "high"
            },
            "completeness": {
                "description": "Complétude de la réponse",
                "enabled": True,
                "severity": "medium"
            }
        }
    
    def set_compliance_rules(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """
        Définit les règles de conformité à appliquer.
        
        Args:
            rules: Dictionnaire des règles de conformité
        """
        self.compliance_rules = rules
    
    def check_medical_advice(self, response: str) -> Dict[str, Any]:
        """
        Vérifie si la réponse contient des conseils médicaux inappropriés.
        
        Args:
            response: Réponse à vérifier
            
        Returns:
            Résultat de la vérification
        """
        prompt = """Vous êtes un expert en conformité médicale. Votre tâche est d'évaluer si la réponse suivante contient des conseils médicaux inappropriés.

Une réponse est considérée comme contenant des conseils médicaux inappropriés si elle :
1. Donne des conseils médicaux spécifiques sans préciser qu'ils doivent être validés par un professionnel de santé
2. Fait des diagnostics ou suggère des traitements
3. Contredit les recommandations médicales standard
4. Présente des opinions médicales comme des faits établis

Réponse à évaluer :
"""
        
        return self._evaluate_rule(prompt, response, "medical_advice")
    
    def check_personal_data(self, response: str) -> Dict[str, Any]:
        """
        Vérifie si la réponse contient des données personnelles non protégées.
        
        Args:
            response: Réponse à vérifier
            
        Returns:
            Résultat de la vérification
        """
        prompt = """Vous êtes un expert en protection des données personnelles. Votre tâche est d'évaluer si la réponse suivante contient des données personnelles non protégées.

Une réponse est considérée comme contenant des données personnelles non protégées si elle :
1. Inclut des numéros de sécurité sociale complets ou partiellement masqués de manière insuffisante
2. Contient des informations médicales sensibles associées à une personne identifiable
3. Révèle des coordonnées personnelles complètes (adresse, téléphone, email)
4. Mentionne des informations financières spécifiques (numéro de compte, montants précis)

Réponse à évaluer :
"""
        
        return self._evaluate_rule(prompt, response, "personal_data")
    
    def check_legal_compliance(self, response: str) -> Dict[str, Any]:
        """
        Vérifie si la réponse est conforme aux exigences légales et réglementaires.
        
        Args:
            response: Réponse à vérifier
            
        Returns:
            Résultat de la vérification
        """
        prompt = """Vous êtes un expert juridique spécialisé dans le domaine de l'assurance santé. Votre tâche est d'évaluer si la réponse suivante est conforme aux exigences légales et réglementaires.

Une réponse est considérée comme non conforme si elle :
1. Contient des informations incorrectes sur les droits des assurés
2. Fait des promesses de couverture ou de remboursement qui pourraient être trompeuses
3. Omet des informations essentielles sur les limitations ou exclusions
4. Suggère des pratiques contraires à la réglementation en vigueur
5. Ne respecte pas les principes de la réforme 100% Santé lorsqu'elle est mentionnée

Réponse à évaluer :
"""
        
        return self._evaluate_rule(prompt, response, "legal_compliance")
    
    def check_tone_politeness(self, response: str) -> Dict[str, Any]:
        """
        Vérifie si le ton et la politesse de la réponse sont appropriés.
        
        Args:
            response: Réponse à vérifier
            
        Returns:
            Résultat de la vérification
        """
        prompt = """Vous êtes un expert en communication client. Votre tâche est d'évaluer si le ton et la politesse de la réponse suivante sont appropriés pour un service client d'assurance santé.

Une réponse est considérée comme inappropriée si elle :
1. Utilise un langage familier ou irrespectueux
2. Manque d'empathie dans des situations qui en nécessitent
3. Est trop directive ou autoritaire
4. Contient des formulations passives-agressives ou condescendantes
5. N'inclut pas les formules de politesse attendues dans une communication professionnelle

Réponse à évaluer :
"""
        
        return self._evaluate_rule(prompt, response, "tone_politeness")
    
    def check_factual_accuracy(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie l'exactitude factuelle de la réponse par rapport au contexte.
        
        Args:
            response: Réponse à vérifier
            context: Contexte de la conversation
            
        Returns:
            Résultat de la vérification
        """
        # Construction du contexte formaté
        context_str = ""
        for key, value in context.items():
            if isinstance(value, dict) or isinstance(value, list):
                context_str += f"\n--- {key} ---\n{json.dumps(value, ensure_ascii=False, indent=2)}\n"
            else:
                context_str += f"\n--- {key} ---\n{value}\n"
        
        prompt = """Vous êtes un expert en vérification factuelle. Votre tâche est d'évaluer si la réponse suivante est factuellement exacte par rapport au contexte fourni.

Une réponse est considérée comme factuellement inexacte si elle :
1. Contient des informations qui contredisent le contexte fourni
2. Fait des affirmations non étayées par le contexte
3. Déforme ou interprète incorrectement les informations du contexte
4. Invente des détails qui ne sont pas présents dans le contexte

Contexte :
"""
        
        # Ajout du contexte au prompt
        prompt += context_str
        prompt += "\n\nRéponse à évaluer :\n"
        
        return self._evaluate_rule(prompt, response, "factual_accuracy")
    
    def check_completeness(self, response: str, query: str) -> Dict[str, Any]:
        """
        Vérifie si la réponse est complète par rapport à la requête.
        
        Args:
            response: Réponse à vérifier
            query: Requête utilisateur
            
        Returns:
            Résultat de la vérification
        """
        prompt = """Vous êtes un expert en analyse de la qualité des réponses. Votre tâche est d'évaluer si la réponse suivante est complète par rapport à la requête de l'utilisateur.

Une réponse est considérée comme incomplète si elle :
1. Ne répond pas à tous les aspects de la requête
2. Omet des informations essentielles pour une compréhension complète
3. Laisse des questions implicites sans réponse
4. Est trop vague ou générale pour être utile
5. Ne fournit pas les détails pratiques nécessaires (procédures, délais, etc.)

Requête de l'utilisateur :
"""
        
        # Ajout de la requête au prompt
        prompt += query
        prompt += "\n\nRéponse à évaluer :\n"
        
        return self._evaluate_rule(prompt, response, "completeness")
    
    def _evaluate_rule(self, prompt: str, response: str, rule_name: str) -> Dict[str, Any]:
        """
        Évalue une règle de conformité spécifique.
        
        Args:
            prompt: Prompt d'évaluation
            response: Réponse à évaluer
            rule_name: Nom de la règle
            
        Returns:
            Résultat de l'évaluation
        """
        # Vérification si la règle est activée
        rule = self.compliance_rules.get(rule_name)
        if not rule or not rule.get('enabled', False):
            return {
                "rule": rule_name,
                "passed": True,
                "score": 1.0,
                "reason": "Règle désactivée",
                "severity": rule.get('severity', 'low') if rule else 'low'
            }
        
        # Construction du prompt complet
        full_prompt = prompt + response + """

Évaluez la conformité de cette réponse selon les critères ci-dessus et fournissez votre analyse au format JSON :
{
  "passed": true/false,
  "score": 0.0-1.0,
  "reason": "Explication détaillée de votre évaluation",
  "issues": ["Liste des problèmes spécifiques identifiés"]
}
"""
        
        # Appel à l'API Groq
        messages = [
            {"role": "system", "content": full_prompt}
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
                        logger.error(f"Impossible d'extraire le JSON de l'évaluation pour la règle {rule_name}")
                        evaluation = {
                            "passed": False,
                            "score": 0.0,
                            "reason": "Erreur d'analyse de la réponse d'évaluation",
                            "issues": ["Format de réponse invalide"]
                        }
                else:
                    evaluation = {
                        "passed": False,
                        "score": 0.0,
                        "reason": "Erreur d'analyse de la réponse d'évaluation",
                        "issues": ["Format de réponse invalide"]
                    }
            
            # Ajout des informations de la règle
            evaluation["rule"] = rule_name
            evaluation["severity"] = rule.get('severity', 'low')
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la règle {rule_name}: {e}")
            
            return {
                "rule": rule_name,
                "passed": False,
                "score": 0.0,
                "reason": f"Erreur technique lors de l'évaluation: {str(e)}",
                "issues": ["Erreur technique"],
                "severity": rule.get('severity', 'low')
            }
    
    def evaluate_response(self, response: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Évalue une réponse complète selon toutes les règles de conformité activées.
        
        Args:
            response: Réponse à évaluer
            query: Requête utilisateur
            context: Contexte de la conversation
            
        Returns:
            Résultat complet de l'évaluation
        """
        context = context or {}
        results = {}
        
        # Évaluation de chaque règle activée
        if self.compliance_rules.get('medical_advice', {}).get('enabled', False):
            results['medical_advice'] = self.check_medical_advice(response)
        
        if self.compliance_rules.get('personal_data', {}).get('enabled', False):
            results['personal_data'] = self.check_personal_data(response)
        
        if self.compliance_rules.get('legal_compliance', {}).get('enabled', False):
            results['legal_compliance'] = self.check_legal_compliance(response)
        
        if self.compliance_rules.get('tone_politeness', {}).get('enabled', False):
            results['tone_politeness'] = self.check_tone_politeness(response)
        
        if self.compliance_rules.get('factual_accuracy', {}).get('enabled', False):
            results['factual_accuracy'] = self.check_factual_accuracy(response, context)
        
        if self.compliance_rules.get('completeness', {}).get('enabled', False):
            results['completeness'] = self.check_completeness(response, query)
        
        # Calcul du résultat global
        passed = True
        high_severity_issues = []
        medium_severity_issues = []
        low_severity_issues = []
        
        for rule_name, result in results.items():
            if not result.get('passed', False):
                severity = result.get('severity', 'low')
                issues = result.get('issues', [])
                
                if severity == 'high':
                    passed = False
                    high_severity_issues.extend(issues)
                elif severity == 'medium':
                    medium_severity_issues.extend(issues)
                else:
                    low_severity_issues.extend(issues)
        
        # Calcul du score global (moyenne pondérée)
        total_weight = 0
        weighted_score = 0
        
        for rule_name, result in results.items():
            severity = result.get('severity', 'low')
            score = result.get('score', 0.0)
            
            if severity == 'high':
                weight = 3
            elif severity == 'medium':
                weight = 2
            else:
                weight = 1
            
            weighted_score += score * weight
            total_weight += weight
        
        global_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "passed": passed,
            "global_score": global_score,
            "high_severity_issues": high_severity_issues,
            "medium_severity_issues": medium_severity_issues,
            "low_severity_issues": low_severity_issues,
            "rule_results": results
        }
    
    def fix_response(self, response: str, evaluation: Dict[str, Any], query: str, context: Dict[str, Any] = None) -> str:
        """
        Corrige une réponse qui n'a pas passé l'évaluation de conformité.
        
        Args:
            response: Réponse originale
            evaluation: Résultat de l'évaluation
            query: Requête utilisateur
            context: Contexte de la conversation
            
        Returns:
            Réponse corrigée
        """
        if evaluation.get('passed', True):
            # Si la réponse a passé l'évaluation, pas besoin de correction
            return response
        
        # Construction des instructions de correction
        instructions = "Votre tâche est de corriger la réponse suivante pour résoudre les problèmes de conformité identifiés.\n\n"
        
        # Ajout des problèmes identifiés
        if evaluation.get('high_severity_issues'):
            instructions += "Problèmes critiques à corriger :\n"
            for issue in evaluation.get('high_severity_issues'):
                instructions += f"- {issue}\n"
            instructions += "\n"
        
        if evaluation.get('medium_severity_issues'):
            instructions += "Problèmes importants à corriger :\n"
            for issue in evaluation.get('medium_severity_issues'):
                instructions += f"- {issue}\n"
            instructions += "\n"
        
        if evaluation.get('low_severity_issues'):
            instructions += "Problèmes mineurs à améliorer :\n"
            for issue in evaluation.get('low_severity_issues'):
                instructions += f"- {issue}\n"
            instructions += "\n"
        
        # Ajout des détails spécifiques par règle
        instructions += "Détails des problèmes par catégorie :\n"
        for rule_name, result in evaluation.get('rule_results', {}).items():
            if not result.get('passed', True):
                instructions += f"\n{result.get('rule', rule_name)} : {result.get('reason', 'Problème non spécifié')}\n"
        
        # Construction du prompt complet
        prompt = f"""Vous êtes un expert en conformité dans le domaine de l'assurance santé. {instructions}

Requête originale de l'utilisateur :
{query}

Réponse à corriger :
{response}

Veuillez fournir une version corrigée de la réponse qui :
1. Résout tous les problèmes de conformité identifiés
2. Maintient le contenu informatif de la réponse originale
3. Reste fidèle à l'intention de la réponse originale
4. Est professionnelle, précise et adaptée au contexte d'assurance santé

Réponse corrigée :
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
            corrected_response = api_response['choices'][0]['message']['content']
            
            return corrected_response
        
        except Exception as e:
            logger.error(f"Erreur lors de la correction de la réponse: {e}")
            
            # En cas d'erreur, ajout d'un avertissement à la réponse originale
            return response + "\n\n[Note: Cette réponse peut contenir des problèmes de conformité qui n'ont pas pu être corrigés automatiquement.]"

# Exemple d'utilisation du système de gating
def example_usage():
    """Exemple d'utilisation du système de gating."""
    # Création du système de gating
    gating = GatingSystem()
    
    # Exemple de réponse à évaluer
    response = """Bonjour Monsieur Dupont,

D'après votre numéro de sécurité sociale 175042789456712, je vois que vous êtes couvert par notre contrat Premium. Pour votre problème de dos, je vous recommande de prendre des anti-inflammatoires et de consulter un ostéopathe. Nous rembourserons 100% de ces frais.

Vous pouvez également ajouter votre nouveau-né à votre contrat sans délai de carence. Envoyez-nous simplement son acte de naissance et nous nous occuperons de tout.

Cordialement,
AssurSanté"""
    
    # Requête utilisateur
    query = "Je viens d'avoir un bébé et j'ai des douleurs au dos. Comment puis-je l'ajouter à mon contrat et est-ce que mes soins seront remboursés ?"
    
    # Contexte
    context = {
        "client": {
            "nom": "Dupont",
            "prenom": "Jean",
            "numero_securite_sociale": "175042789456712",
            "contrats": [
                {
                    "type": "Santé Famille",
                    "niveau": "Premium",
                    "statut": "Actif"
                }
            ]
        }
    }
    
    # Évaluation de la réponse
    print("Évaluation de la réponse...")
    evaluation = gating.evaluate_response(response, query, context)
    
    # Affichage du résultat
    print(f"Évaluation passée : {evaluation.get('passed')}")
    print(f"Score global : {evaluation.get('global_score'):.2f}")
    
    if not evaluation.get('passed'):
        print("\nProblèmes critiques :")
        for issue in evaluation.get('high_severity_issues', []):
            print(f"- {issue}")
        
        # Correction de la réponse
        print("\nCorrection de la réponse...")
        corrected_response = gating.fix_response(response, evaluation, query, context)
        
        print("\nRéponse corrigée :")
        print(corrected_response)

if __name__ == "__main__":
    example_usage()
