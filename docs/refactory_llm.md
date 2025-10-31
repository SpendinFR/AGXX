# Refactory LLM – état d'avancement

## Objectif
Mettre fin aux pipelines heuristiques multi-étapes et remplacer chaque fonctionnalité par un appel LLM unique, avec seulement des adaptations légères côté Python (normalisation d'entrée, validation de sortie, persistance). Les modules déjà traités illustrent ce modèle : ils ne conservent plus que le code nécessaire pour préparer le prompt, invoquer le contrat LLM et appliquer le résultat structuré.

## Modules déjà refondus
- **Langage – compréhension** : `SemanticUnderstanding` prépare l’énoncé, appelle `language_understanding` une seule fois et met à jour l’état de dialogue avec la réponse normalisée.【F:AGI_Evolutive/language/understanding.py†L1-L256】
- **Langage – génération** : `LanguageGeneration` construit un `NLGRequest`, invoque `language_nlg` et fournit directement le message, les sections et les signaux de sécurité retournés.【F:AGI_Evolutive/language/nlg.py†L1-L189】
- **Ingestion I/O** : l’`IntentIngestionOrchestrator` remplace la pile de patterns/ML par un unique appel `intent_ingestion` et renvoie un `IntentIngestionResult` complet.【F:AGI_Evolutive/io/intent_classifier.py†L1-L159】
- **Conversation** : `ContextBuilder` collecte l’historique minimal, appelle `conversation_context` et expose la réponse structurée sans caches ni trackers heuristiques.【F:AGI_Evolutive/conversation/context.py†L200-L315】
- **Mémoire – concepts** : `ConceptExtractor` lotit les souvenirs récents, appelle `concept_extraction` une fois et propage les concepts/relations vers le store.【F:AGI_Evolutive/memory/concept_extractor.py†L320-L406】
- **Mémoire – résumés** : `ProgressiveSummarizer` agrège les souvenirs, déclenche `memory_summarizer` et persiste les digests renvoyés par le modèle.【F:AGI_Evolutive/memory/summarizer.py†L240-L306】
- **Retrieval/RAG** : `RAGAdaptiveController` formate la requête, invoque `retrieval_orchestrator` pour le plan et gère feedback/activation via le même contrat.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L168-L240】
- **Cognition – planner** : le nouveau `Planner` s’appuie exclusivement sur `planner_support` pour générer plans et étapes, puis stocke le JSON reçu.【F:AGI_Evolutive/cognition/planner.py†L1-L308】
- **Cognition – priorisation/context** : `GoalPrioritizer`, `infer_where_and_apply`, `Homeostasis` et `recommend_and_apply_mission` centralisent chacun leur logique métier dans une réponse LLM unique avant de mettre à jour l’état local.【F:AGI_Evolutive/cognition/prioritizer.py†L168-L240】【F:AGI_Evolutive/cognition/context_inference.py†L16-L120】【F:AGI_Evolutive/cognition/homeostasis.py†L120-L237】【F:AGI_Evolutive/cognition/identity_mission.py†L146-L202】
- **Raisonnement** : `run_reasoning_episode` assemble contexte/outillage, appelle `reasoning_episode` une fois et restitue la directive complète pour le système de raisonnement.【F:AGI_Evolutive/reasoning/strategies.py†L1-L405】【F:AGI_Evolutive/reasoning/__init__.py†L94-L178】
- **Documentation & contrats** : `docs/llm_runtime_contracts.md` trace désormais chaque contrat LLM actif et ses champs attendus pour faciliter l’observabilité et la poursuite de la refonte.【F:docs/llm_runtime_contracts.md†L1-L159】

## Modules restant à traiter
Plusieurs sous-systèmes conservent encore des politiques adaptatives, bandits ou EMAs multiples et devront être remplacés par des orchestrateurs LLM similaires :
- **Autonomie** : `AutonomyCore` maintient un logistic-regression maison, des EMAs et des règles combinatoires avant de requêter le LLM en fin de chaîne.【F:AGI_Evolutive/autonomy/core.py†L25-L160】
- **Auto-amélioration** : `code_evolver.py` pilote encore des learners heuristiques (`OnlineHeuristicLearner`, `_ScoreHeuristicTweaker`) au lieu de déléguer l’évaluation complète au modèle.【F:AGI_Evolutive/self_improver/code_evolver.py†L1-L160】
- **Autres domaines** : vérifier `autonomy/auto_evolution.py`, `beliefs/`, `learning/`, `runtime/`, `social/`, `world_model/` et `perception/` pour remplacer les boucles statistiques restantes par des appels LLM unifiés suivant le même pattern (payload normalisé → `call_dict` → application du JSON).

## Procédure pour poursuivre la refonte
1. **Cartographier le module** : identifier les points d’entrée publics et la séquence d’actions actuellement enchaînée.
2. **Déterminer le contrat** : définir le payload et la sortie JSON cibles que le LLM pourra fournir en un seul aller-retour, en s’appuyant sur les exemples existants.
3. **Implémenter l’orchestrateur** : créer une classe/dataclass qui prépare le payload, appelle `get_llm_manager().call_dict` (ou `try_call_llm_dict`) et valide/normalise la réponse.
4. **Supprimer les heuristiques** : retirer bandits, EMAs, modèles locaux et fallbacks pour s’aligner sur l’approche « LLM ou rien ».
5. **Mettre à jour la documentation** : ajouter ou compléter les entrées correspondantes dans `docs/llm_runtime_contracts.md` et dans l’inventaire des points d’entrée si nécessaire.
6. **Journalisation et persistance** : conserver des traces structurées du payload et du résultat, comme dans les modules déjà refondus, pour faciliter audit et débogage.

## Où reprendre
Reprendre par l’autonomie (scheduler idle, auto-signaux), puis enchaîner sur l’auto-amélioration et le monde social/modèle du monde, en appliquant exactement le gabarit déjà mis en œuvre : payload minimal, un appel LLM, application directe du résultat.
