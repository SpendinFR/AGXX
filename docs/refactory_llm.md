# Refactory LLM – point d'arrêt courant

## Objectif général
Remplacer progressivement chaque pipeline heuristique du dépôt par un unique orchestrateur `get_llm_manager().call_dict`. Chaque module doit se limiter à :
1. préparer un payload propre et auto-documenté ;
2. appeler le contrat LLM référencé dans `AGI_Evolutive/utils/llm_specs.py` ;
3. appliquer la réponse JSON normalisée sans logique parallèle ni fallback local.

## Domaines déjà migrés
La refonte « un appel LLM par fonctionnalité » est effective pour les blocs suivants :
- **Autonomie & auto-amélioration** – `autonomy/core.py`, `autonomy/auto_evolution.py`, `autonomy/auto_signals.py`, `self_improver/code_evolver.py` et la façade mémoire s'appuient uniquement sur leurs contrats `autonomy_core`, `auto_evolution`, `auto_signal_*` et `code_evolver`.
- **Croyances & connaissances** – Le graphe de croyances et ses satellites (entity linker, enrichissement d'ontologie, résumés) appellent `belief_graph_orchestrator`, `entity_linker`, `ontology_enrichment` et `belief_summarizer` pour toutes les mises à jour.
- **Apprentissage** – Les cycles expérientiels, méta-contrôleurs et transferts de connaissances sont réduits à leurs orchestrateurs LLM (`experiential_learning_cycle`, `learning_meta_controller`, etc.).
- **Social** – Adaptive lexicon, interaction miner, critic et tactic selector agrègent leurs inputs et délèguent la décision à leurs specs `social_*`.
- **Runtime, perception & world model** – Analytics, scheduler, job manager, monitoring, phenomenal kernel, dash, response formatter, perception module et façades du world model ne conservent que la préparation de payload et l'application de la réponse LLM.
- **Documentation & specs** – `utils/llm_specs.py` et `docs/llm_runtime_contracts.md` recensent tous les contrats actifs avec exemples et champs requis.

## Point d'arrêt
Nous marquons une pause après la migration des domaines Runtime/Perception/World Model. Les contrats LLM correspondants sont documentés et les orchestrateurs en production utilisent exclusivement `call_dict`.

## Chantiers à poursuivre lors de la reprise
Ces zones n'ont pas encore été converties ou nécessitent une seconde passe pour éliminer les heuristiques résiduelles :
- **Conversation & langage amont** – vérifier le pipeline d'ingestion, les dialogues et les outils de rendu restants.
- **Cognition, planning & goals** – remplacer les derniers contrôleurs hybrides (planner HTN, goal prioritizer, homeostasis, reasoning episodes) par des orchestrateurs LLM sans fallback.
- **Créativité, émotions, phénoménologie & métacognition** – auditer chaque module pour identifier les helpers procéduraux encore actifs et les migrer vers un unique appel contractuel.
- **Action/agents externes** – uniformiser les interfaces d'action et de scheduling léger en déléguant la décision au LLM.
- **Tests & observabilité** – ajouter/mettre à jour des tests d'intégration ciblés pour s'assurer que les orchestrateurs consomment correctement les réponses LLM et que la journalisation reste structurée.

## Checklist pour chaque nouveau chantier
1. Cartographier les points d'entrée publics et les étapes legacy.
2. Définir ou mettre à jour le contrat correspondant dans `llm_specs.py` (+ documentation).
3. Implémenter l'orchestrateur fin, supprimer les heuristiques et fallbacks.
4. Journaliser payload et sortie (niveau DEBUG/INFO) pour auditabilité.
5. Rafraîchir la documentation (`docs/llm_runtime_contracts.md`, ce fichier) une fois le domaine migré.

## Pour la prochaine session
- Repartir de la section « Chantiers à poursuivre » ci-dessus.
- Noter dans ce document tout domaine finalisé ou toute nouvelle décision de design.
- Conserver la règle d'or : **un contrat LLM par fonctionnalité métier**.
