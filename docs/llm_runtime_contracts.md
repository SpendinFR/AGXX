# Contrats critiques des sorties LLM

Ce référentiel décrit, pour chaque appel LLM encore actif dans le runtime, les champs exacts
qu’attendent les modules. Les tableaux résument les contraintes de forme ainsi que l’effet
produit lorsque le modèle respecte (ou non) le contrat. Utilise-les pour auditer rapidement les
spécifications de prompts et vérifier que les réponses générées restent compatibles.

## Ingestion I/O

### `intent_ingestion` — `AGI_Evolutive/io/intent_classifier.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `intent.label` | `str` non vide | Oui | Normalisé en majuscules pour piloter les couches amont.【F:AGI_Evolutive/io/intent_classifier.py†L70-L99】 |
| `intent.confidence` | nombre ∈ [0, 1] | Oui | Clampé via `_coerce_float` pour alimenter la confiance globale.【F:AGI_Evolutive/io/intent_classifier.py†L100-L134】 |
| `intent.rationale` | `str` | Non | Conserve la justification brute dans le résultat.【F:AGI_Evolutive/io/intent_classifier.py†L100-L134】 |
| `tone`/`sentiment`/`priority`/`urgency` | `str` | Non | Restitués tels quels pour guider la modulation conversationnelle.【F:AGI_Evolutive/io/intent_classifier.py†L105-L116】 |
| `summary` | `str` | Non | Utilisable tel quel pour un aperçu synthétique de la requête.【F:AGI_Evolutive/io/intent_classifier.py†L114-L116】 |
| `follow_up_questions` | liste de `str` | Non | Normalisées dans un tuple pour déclencher d'éventuelles relances.【F:AGI_Evolutive/io/intent_classifier.py†L118-L125】 |
| `safety.flags` | liste de `str` | Non | Converties en tuple ordonné pour aiguiller les garde-fous applicatifs.【F:AGI_Evolutive/io/intent_classifier.py†L126-L134】 |
| `entities` | liste de mappings | Non | Chaque mapping est figé via `MappingProxyType` pour rester immuable.【F:AGI_Evolutive/io/intent_classifier.py†L136-L158】 |

## Conversation

### `conversation_context` — `AGI_Evolutive/conversation/context.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | liste de `str` | Non | Restituée telle quelle pour alimenter les vues conversationnelles.【F:AGI_Evolutive/conversation/context.py†L154-L164】 |
| `summary_text` | `str` | Non | Reprise comme synthèse courte si fournie.【F:AGI_Evolutive/conversation/context.py†L150-L165】 |
| `topics` | liste de `str` | Non | Alimente directement la modulation stylistique et les UIs.【F:AGI_Evolutive/conversation/context.py†L166-L178】 |
| `key_moments` | liste de `str` | Non | Réutilisée pour les rappels « lien au passé » du renderer.【F:AGI_Evolutive/conversation/context.py†L168-L172】 |
| `user_style` | mapping clé/valeur | Non | Copié pour guider la modulation de la voix et l'affichage.【F:AGI_Evolutive/conversation/context.py†L173-L177】 |
| `follow_up_questions` | liste de `str` | Non | Déposée telle quelle pour déclencher des relances automatiques.【F:AGI_Evolutive/conversation/context.py†L173-L176】 |
| `recommended_actions` | liste de mappings | Non | Fournit les actions suggérées par le LLM aux couches amont.【F:AGI_Evolutive/conversation/context.py†L173-L176】 |
| `alerts` | liste de `str` | Non | Transmises aux composants de monitoring/sécurité.【F:AGI_Evolutive/conversation/context.py†L173-L176】 |
| `tone` | `str` | Non | Sert à la modulation de style à l'exécution.【F:AGI_Evolutive/conversation/context.py†L173-L177】 |
| `llm_summary` | mapping | Oui (implicite) | Archive brute de la réponse pour audit et instrumentation.【F:AGI_Evolutive/conversation/context.py†L179-L185】 |
| `llm_topics` | liste de mappings | Non | Préserve le détail structuré (label/rang) fourni par le modèle.【F:AGI_Evolutive/conversation/context.py†L180-L184】 |

## Social

### `social_interaction_context` — `AGI_Evolutive/social/interaction_rule.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `baseline` | mapping | Oui | Sert de fallback local si la réponse LLM est vide (`ContextBuilder.snapshot`).【F:AGI_Evolutive/social/interaction_rule.py†L120-L143】 |
| `context` | mapping | Oui | Transmis tel quel à `TacticSelector.pick` pour guider la décision de tactique.【F:AGI_Evolutive/social/interaction_rule.py†L104-L143】【F:AGI_Evolutive/social/tactic_selector.py†L24-L47】 |
| `signals` | mapping | Non | Journalisé avec le contexte pour éclairer la sélection (valence, risque).【F:AGI_Evolutive/social/interaction_rule.py†L126-L143】【F:AGI_Evolutive/social/tactic_selector.py†L31-L47】 |
| `topics` | liste de `str` | Non | Propagée telle quelle pour enrichir la mémoire et les traces de décision.【F:AGI_Evolutive/social/interaction_rule.py†L132-L143】【F:AGI_Evolutive/language/renderer.py†L513-L546】 |
| `notes` | `str` | Non | Conserve la justification du modèle pour audit humain.【F:AGI_Evolutive/social/interaction_rule.py†L126-L143】 |

### `social_interaction_miner` — `AGI_Evolutive/social/interaction_miner.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `rules` | liste de mappings | Oui | Chaque élément est converti en :class:`InteractionRule` et stocké dans la mémoire sociale.【F:AGI_Evolutive/social/interaction_miner.py†L40-L89】 |
| `rules[*].id` | `str` | Oui | Identifiant persistant utilisé pour les mises à jour futures et la planification de validation.【F:AGI_Evolutive/social/interaction_miner.py†L40-L89】【F:AGI_Evolutive/core/document_ingest.py†L324-L361】 |
| `rules[*].tactic` | mapping | Oui | Reconstruit en :class:`TacticSpec` puis transmis aux sélecteurs et critiques.【F:AGI_Evolutive/social/interaction_rule.py†L61-L101】【F:AGI_Evolutive/social/interaction_miner.py†L40-L89】 |
| `rules[*].predicates` | liste de mappings | Oui | Normalisées en :class:`Predicate` pour contextualiser l'application de la règle.【F:AGI_Evolutive/social/interaction_rule.py†L45-L83】【F:AGI_Evolutive/social/interaction_miner.py†L40-L89】 |
| `notes` | `str` | Non | Archivé dans les traces d'induction pour documenter l'analyse du modèle.【F:AGI_Evolutive/social/interaction_miner.py†L60-L89】 |

### `social_rule_self_evaluation` — `AGI_Evolutive/social/interaction_miner.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `actions` | liste de mappings | Oui | Planifiées telles quelles par le job manager pour vérifier la règle récemment extraite.【F:AGI_Evolutive/social/interaction_miner.py†L51-L75】【F:AGI_Evolutive/core/document_ingest.py†L344-L360】 |
| `actions[*].label` | `str` | Oui | Sert de description dans les jobs planifiés et les journaux de validation.【F:AGI_Evolutive/social/interaction_miner.py†L51-L75】 |
| `actions[*].priority` | nombre ∈ [0, 1] | Non | Transmis pour ordonner les tâches de validation asynchrones.【F:AGI_Evolutive/social/interaction_miner.py†L51-L75】 |
| `notes` | `str` | Non | Ajouté aux traces pour contextualiser la recommandation du modèle.【F:AGI_Evolutive/social/interaction_miner.py†L51-L75】 |

### `social_tactic_selector` — `AGI_Evolutive/social/tactic_selector.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `selected_rule` | mapping | Oui | Converti en :class:`InteractionRule` puis persisté/registré comme tactique appliquée.【F:AGI_Evolutive/social/tactic_selector.py†L19-L49】【F:AGI_Evolutive/language/renderer.py†L513-L546】 |
| `meta.utility` | nombre ∈ [0, 1] | Non | Journalisé pour documenter pourquoi la tactique a été retenue.【F:AGI_Evolutive/social/tactic_selector.py†L33-L47】 |
| `meta.risk` | nombre ∈ [0, 1] | Non | Transmis dans la trace de décision pour calibrer les garde-fous sociaux.【F:AGI_Evolutive/social/tactic_selector.py†L33-L47】【F:AGI_Evolutive/language/renderer.py†L513-L546】 |
| `meta.rationale` | `str` | Non | Conserve la justification du modèle pour revue humaine.【F:AGI_Evolutive/social/tactic_selector.py†L33-L47】 |

### `social_adaptive_lexicon` — `AGI_Evolutive/social/adaptive_lexicon.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `matched` | booléen | Oui | Retour immédiat de `AdaptiveLexicon.match` pour indiquer la détection d’un marqueur.【F:AGI_Evolutive/social/adaptive_lexicon.py†L77-L117】 |
| `state.tokens` | liste de mappings | Oui | Persiste les entrées actives du lexique dans l’architecture (`_adaptive_lexicon_state`).【F:AGI_Evolutive/social/adaptive_lexicon.py†L37-L74】【F:AGI_Evolutive/social/adaptive_lexicon.py†L94-L110】 |
| `state.dormant_tokens` | liste de mappings | Non | Permet de conserver les expressions mises en sommeil par le modèle.【F:AGI_Evolutive/social/adaptive_lexicon.py†L37-L74】【F:AGI_Evolutive/social/adaptive_lexicon.py†L94-L110】 |
| `updates` | liste de mappings | Non | Reflète les renforcements proposés par le modèle (utilisé par les UIs/reporting).【F:AGI_Evolutive/social/adaptive_lexicon.py†L94-L117】 |
| `notes` | `str` | Non | Consigné dans `last_response` pour faciliter les audits linguistiques.【F:AGI_Evolutive/social/adaptive_lexicon.py†L111-L117】 |

### `social_interaction_outcome` — `AGI_Evolutive/social/social_critic.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `reward` | nombre ∈ [0, 1] | Oui | Clampé et journalisé comme score social final.【F:AGI_Evolutive/social/social_critic.py†L77-L123】【F:AGI_Evolutive/social/social_critic.py†L125-L152】 |
| `confidence` | nombre ∈ [0, 1] | Oui | Conserve la fiabilité du diagnostic et alimente les rapports métacognitifs.【F:AGI_Evolutive/social/social_critic.py†L77-L142】 |
| `signals` | mapping | Oui | Diffusé tel quel aux consommateurs (scheduler, monitoring) pour contextualiser l’outcome.【F:AGI_Evolutive/social/social_critic.py†L103-L142】【F:AGI_Evolutive/runtime/scheduler.py†L814-L821】 |
| `lexicon_updates` | liste de mappings | Non | Remonté aux surfaces produit pour actualiser le vocabulaire préféré.【F:AGI_Evolutive/social/social_critic.py†L103-L142】【F:AGI_Evolutive/language/renderer.py†L351-L359】 |
| `notes` | `str` | Non | Stocké pour audit dans la mémoire (`social_outcome`).【F:AGI_Evolutive/social/social_critic.py†L125-L152】 |

### `social_conversation_analysis` — `AGI_Evolutive/social/social_critic.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Oui | Fournit une synthèse courte utilisée par les vues d'observation sociale.【F:AGI_Evolutive/social/social_critic.py†L90-L102】 |
| `risks` / `opportunities` | liste de `str` | Non | Restituées directement pour informer les opérateurs ou déclencher des follow-ups.【F:AGI_Evolutive/social/social_critic.py†L90-L102】 |
| `recommended_actions` | liste de mappings | Non | Peut être transmis au planner pour instrumentation humaine.【F:AGI_Evolutive/social/social_critic.py†L90-L102】 |
| `notes` | `str` | Non | Aide-mémoire pour expliquer les observations du modèle.【F:AGI_Evolutive/social/social_critic.py†L90-L102】 |

### `social_conversation_rewrite` — `AGI_Evolutive/social/social_critic.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `rewritten` | `str` | Oui | Remplace le texte initial lorsqu'une reformulation sociale est demandée.【F:AGI_Evolutive/social/social_critic.py†L102-L113】 |
| `justification` | `str` | Non | Conservée pour expliquer les modifications apportées par le LLM.【F:AGI_Evolutive/social/social_critic.py†L102-L113】 |

### `social_rule_update` — `AGI_Evolutive/social/social_critic.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `rule` | mapping | Oui | Converti en :class:`InteractionRule` puis persisté dans la mémoire sociale.【F:AGI_Evolutive/social/social_critic.py†L113-L152】 |
| `rule.id` | `str` | Oui | Permet de retrouver et écraser la règle existante correspondante.【F:AGI_Evolutive/social/social_critic.py†L128-L152】 |
| `notes` | `str` | Non | Stocké aux côtés de la règle pour documenter l'évolution proposée.【F:AGI_Evolutive/social/social_critic.py†L128-L152】 |

### `social_simulation_score` — `AGI_Evolutive/social/social_critic.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `score` | nombre ∈ [0, 1] | Oui | Restitué par `SocialCritic.score` pour comparer scénarios avec/sans mécanisme testé.【F:AGI_Evolutive/social/social_critic.py†L113-L123】【F:AGI_Evolutive/cognition/principle_inducer.py†L662-L663】 |
| `rationale` | `str` | Non | Conserve l'explication du modèle pour guidage des expérimentations.【F:AGI_Evolutive/social/social_critic.py†L113-L123】 |
| `signals` | mapping | Non | Permet d'inspecter les métriques clefs dérivées de la simulation.【F:AGI_Evolutive/social/social_critic.py†L113-L123】 |

## Autonomie

### `autonomy_core` — `AGI_Evolutive/autonomy/core.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `hypotheses` | liste de mappings (`content`, `prior`) | Oui | Converties en :class:`Hypothesis`; une hypothèse par défaut est ajoutée si la liste est vide.【F:AGI_Evolutive/autonomy/core.py†L68-L115】【F:AGI_Evolutive/autonomy/core.py†L212-L224】 |
| `tests` | liste de mappings (`description`, `cost_est`, `expected_information_gain`) | Oui | Transformées en :class:`Test`; une action minimale est générée en fallback.【F:AGI_Evolutive/autonomy/core.py†L118-L146】【F:AGI_Evolutive/autonomy/core.py†L212-L224】 |
| `evidence` | mapping (`notes`, `confidence`) | Oui | Normalisée en :class:`Evidence` injectée dans `episode_record`.【F:AGI_Evolutive/autonomy/core.py†L149-L158】【F:AGI_Evolutive/autonomy/core.py†L217-L228】 |
| `decision` | mapping | Oui | Archivée dans les journaux et sert de source de feedback éventuel vers la policy.【F:AGI_Evolutive/autonomy/core.py†L212-L226】【F:AGI_Evolutive/autonomy/core.py†L301-L324】 |
| `progress_step` | nombre ∈ [0, 1] | Oui | Transmis à `GoalDAG.bump_progress` pour incrémenter l’objectif courant.【F:AGI_Evolutive/autonomy/core.py†L200-L209】【F:AGI_Evolutive/autonomy/core.py†L239-L247】 |
| `final_confidence` | nombre ∈ [0, 1] | Non | Renseigne `final_confidence` dans `episode_record`; défaut sur la confiance de la preuve.【F:AGI_Evolutive/autonomy/core.py†L173-L187】【F:AGI_Evolutive/autonomy/core.py†L212-L224】 |
| `result_text` | `str` | Non | Texte résumé injecté dans l’épisode pour audit.【F:AGI_Evolutive/autonomy/core.py†L177-L186】【F:AGI_Evolutive/autonomy/core.py†L212-L224】 |
| `metacognition_event` | mapping | Non | Relayé à `metacognition._record_metacognitive_event` si disponible.【F:AGI_Evolutive/autonomy/core.py†L189-L208】【F:AGI_Evolutive/autonomy/core.py†L264-L276】 |
| `policy_feedback` | mapping | Non | Transmis à `policy.register_outcome` pour informer la boucle legacy.【F:AGI_Evolutive/autonomy/core.py†L189-L208】【F:AGI_Evolutive/autonomy/core.py†L278-L324】 |
| `annotations` | mapping | Non | Ajouté tel quel dans `autonomy.tick` pour instrumentation et audit.【F:AGI_Evolutive/autonomy/core.py†L189-L208】【F:AGI_Evolutive/autonomy/core.py†L212-L226】 |

### `auto_evolution` — `AGI_Evolutive/autonomy/auto_evolution.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `accepted` | booléen | Oui | Détermine si l’intention proposée doit être promue immédiatement.【F:AGI_Evolutive/autonomy/auto_evolution.py†L78-L128】【F:AGI_Evolutive/autonomy/auto_evolution.py†L170-L214】 |
| `intention` | mapping | Oui | Recopié dans `AutoEvolutionOutcome.intention` et transmis au registre de signaux (action_type/description).【F:AGI_Evolutive/autonomy/auto_evolution.py†L82-L131】【F:AGI_Evolutive/autonomy/auto_evolution.py†L212-L221】 |
| `intention.action_type` | `str` | Oui | Sert de clé pour enregistrer les signaux dérivés via `AutoSignalRegistry.register`.【F:AGI_Evolutive/autonomy/auto_evolution.py†L214-L221】 |
| `intention.description` | `str` | Non | Journalisé tel quel pour contextualiser la décision automatique.【F:AGI_Evolutive/autonomy/auto_evolution.py†L214-L221】 |
| `intention.confidence` | nombre ∈ [0, 1] | Non | Utilisé pour calibrer la confiance globale associée à l'intention proposée.【F:AGI_Evolutive/autonomy/auto_evolution.py†L78-L128】 |
| `evaluation` | mapping | Oui | Normalisé et utilisé pour contextualiser les signaux enregistrés par le LLM.【F:AGI_Evolutive/autonomy/auto_evolution.py†L83-L132】【F:AGI_Evolutive/autonomy/auto_evolution.py†L214-L221】 |
| `evaluation.score` / `impact` | nombre ou `str` | Non | Instrumentés dans les logs pour suivre la sévérité ou l'effet attendu de l'intention.【F:AGI_Evolutive/autonomy/auto_evolution.py†L78-L133】 |
| `signals` | liste de mappings | Non | Chaque élément est renvoyé au `AutoSignalRegistry` via `register` pour être persisté et suivi.【F:AGI_Evolutive/autonomy/auto_evolution.py†L84-L133】【F:AGI_Evolutive/autonomy/auto_evolution.py†L206-L223】 |
| `signals[*].metric` | `str` | Oui | Sert de clé principale pour dédupliquer/mettre à jour le signal existant.【F:AGI_Evolutive/autonomy/auto_signals.py†L40-L88】 |
| `signals[*].direction` | `str` (`above`/`below`) | Non | Détermine la polarité lors de la conversion en :class:`AutoSignal`.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].target` | nombre | Non | Stocké dans `AutoSignal.target` pour guider l'objectif numérique.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].weight` | nombre | Non | Transmis à `AutoSignal.weight` pour pondérer les observations futures.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `follow_up` | liste de `str` | Non | Conserve les actions de suivi recommandées par le modèle (stockées dans `AutoEvolutionOutcome.follow_up`).【F:AGI_Evolutive/autonomy/auto_evolution.py†L85-L117】【F:AGI_Evolutive/autonomy/auto_evolution.py†L134-L141】 |
| `metadata` | mapping | Non | Archivé tel quel dans l’issue LLM pour instrumentation et audit ultérieur.【F:AGI_Evolutive/autonomy/auto_evolution.py†L86-L118】【F:AGI_Evolutive/autonomy/auto_evolution.py†L117-L128】 |

## Croyances

### `belief_graph_orchestrator` — `AGI_Evolutive/beliefs/graph.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `result.operation` | `str` | Non | Journalisé pour instrumentation lors des retours LLM.【F:AGI_Evolutive/beliefs/graph.py†L310-L330】 |
| `result.belief_id` | `str` | Oui (opérations `upsert_belief` / `add_evidence`) | Permet de récupérer la croyance normalisée stockée via `_apply_updates`. Absence ⇒ `LLMIntegrationError`.【F:AGI_Evolutive/beliefs/graph.py†L332-L351】 |
| `result.event_id` | `str` | Oui (opération `add_event`) | Utilisé pour renvoyer l’événement consolidé au runtime après `_apply_updates`.【F:AGI_Evolutive/beliefs/graph.py†L386-L402】 |
| `updates.beliefs` | liste de mappings | Non | Chaque entrée est convertie en :class:`Belief` et insérée/écrasée dans le cache local.【F:AGI_Evolutive/beliefs/graph.py†L287-L305】 |
| `updates.events` | liste de mappings | Non | Transformées en :class:`Event` puis persistées dans `_events`.【F:AGI_Evolutive/beliefs/graph.py†L287-L305】 |
| `updates.remove_beliefs` | liste de `str` | Non | Identifiants supprimés du cache, typiquement lors d’un `retire`.【F:AGI_Evolutive/beliefs/graph.py†L293-L299】 |
| `updates.remove_events` | liste de `str` | Non | Purge des événements obsolètes du cache local.【F:AGI_Evolutive/beliefs/graph.py†L300-L305】 |
| `beliefs` | liste de mappings | Non | Retourne les résultats d’une requête structurée (reconvertis en :class:`Belief`).【F:AGI_Evolutive/beliefs/graph.py†L368-L378】 |
| `pairs` | liste de mappings | Non | Paires `positive`/`negative` identifiant les contradictions à remonter. Les identifiants sont résolus via `_beliefs`.【F:AGI_Evolutive/beliefs/graph.py†L355-L365】 |
| `notes` | `str` | Non | Stocké pour audit et remonté aux couches appelantes lors des suivis humains.【F:AGI_Evolutive/beliefs/graph.py†L332-L351】【F:AGI_Evolutive/beliefs/graph.py†L377-L381】 |

### `belief_summarizer` — `AGI_Evolutive/beliefs/summarizer.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `narrative` | `str` | Oui | Restituée telle quelle par `latest_summary` pour les tableaux de bord narratifs.【F:AGI_Evolutive/beliefs/summarizer.py†L39-L66】【F:AGI_Evolutive/beliefs/graph.py†L390-L399】 |
| `anchors` | liste de `str` | Non | Dénote les points d’ancrage principaux diffusés aux modules d’observation.【F:AGI_Evolutive/beliefs/summarizer.py†L45-L64】 |
| `coherence_score` | nombre ∈ [0, 1] | Non | Sert de métrique de cohérence agrégée dans la télémétrie d’autosurveillance.【F:AGI_Evolutive/beliefs/summarizer.py†L45-L64】 |
| `notes` | `str` | Non | Ajoutées aux journaux pour documenter recommandations et suivis humains.【F:AGI_Evolutive/beliefs/summarizer.py†L55-L66】 |
| `raw` | mapping | Non | Conservé pour audit via `BeliefSummarizer.last`.【F:AGI_Evolutive/beliefs/summarizer.py†L22-L63】 |

### `entity_linker` — `AGI_Evolutive/beliefs/entity_linker.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `entity.canonical_id` | `str` non vide | Oui | Clé principale stockée dans `_entities` et retournée aux consommateurs.【F:AGI_Evolutive/beliefs/entity_linker.py†L54-L105】【F:AGI_Evolutive/beliefs/entity_linker.py†L140-L187】 |
| `entity.entity_type` | `str` | Oui | Renseigne le type final retourné par `resolve`/`link`.【F:AGI_Evolutive/beliefs/entity_linker.py†L56-L187】 |
| `entity.confidence` | nombre ∈ [0, 1] | Non | Persiste le niveau de confiance pour instrumentation et merges futurs.【F:AGI_Evolutive/beliefs/entity_linker.py†L56-L110】 |
| `entity.justification` | `str` | Non | Journalisé dans `EntityEntry.raw` pour audit manuel.【F:AGI_Evolutive/beliefs/entity_linker.py†L87-L110】 |
| `entity.aliases` | liste de `str` | Non | Chaque alias est normalisé et indexé dans `_aliases`.【F:AGI_Evolutive/beliefs/entity_linker.py†L105-L122】 |
| `aliases` | liste de `str` | Non | Ajoutées comme alias secondaires après résolution ou merge.【F:AGI_Evolutive/beliefs/entity_linker.py†L110-L122】【F:AGI_Evolutive/beliefs/entity_linker.py†L205-L220】 |
| `notes` | `str` | Non | Renvoyées telles quelles à l’appelant (notes opérateur).【F:AGI_Evolutive/beliefs/entity_linker.py†L171-L181】 |

### `ontology_enrichment` — `AGI_Evolutive/beliefs/ontology.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `entities` | liste de mappings | Non | Chaque entrée est convertie en :class:`EntityType` puis enregistrée.【F:AGI_Evolutive/beliefs/ontology.py†L79-L126】【F:AGI_Evolutive/beliefs/ontology.py†L153-L177】 |
| `entities[*].parent` | `str` | Non | Définit l’ancrage hiérarchique lors de l’enregistrement.【F:AGI_Evolutive/beliefs/ontology.py†L99-L126】 |
| `relations` | liste de mappings | Non | Chaque mapping alimente :class:`RelationType` (domain/range/polarity).【F:AGI_Evolutive/beliefs/ontology.py†L128-L177】 |
| `events` | liste de mappings | Non | Converties en :class:`EventType` pour la gestion des rôles n-aires.【F:AGI_Evolutive/beliefs/ontology.py†L178-L214】 |
| `notes` | `str` | Non | Peut justifier l’absence de suggestion fiable ; conservé tel quel pour audit.【F:AGI_Evolutive/beliefs/ontology.py†L120-L177】 |

### `auto_signal_derivation` — `AGI_Evolutive/autonomy/auto_signals.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `signals` | liste de mappings | Oui | Chaque définition est renvoyée par `AutoSignalRegistry.derive` pour alimenter la promotion d’intentions (avant enregistrement).【F:AGI_Evolutive/autonomy/auto_signals.py†L103-L150】【F:AGI_Evolutive/autonomy/auto_signals.py†L183-L208】 |
| `signals[*].name` | `str` | Non | Sert d'alias lisible pour les journaux et UIs d'autonomie.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].metric` | `str` | Oui | Normalisé via `_ensure_metric` pour garantir une clé persistante côté registre.【F:AGI_Evolutive/autonomy/auto_signals.py†L40-L88】 |
| `signals[*].direction` | `str` (`above`/`below`) | Non | Détermine l'interprétation des futures observations (favoriser ou réduire la valeur).【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].target` | nombre | Non | Guide la valeur attendue ; clampé à float si présent.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].weight` | nombre | Non | Pondération utilisée lors du calcul des récompenses. Clampée si fournie.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].source` | `str` | Non | Conserve l'origine (llm_derivation, historique, etc.) pour l'audit.【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |
| `signals[*].metadata` | mapping | Non | Recopiée telle quelle pour contextualiser les calculs (fenêtre, agrégation).【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】 |

### `auto_signal_registration` — `AGI_Evolutive/autonomy/auto_signals.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `signals` | liste de mappings | Oui | Converties en :class:`AutoSignal` et stockées dans le registre avec leurs observations initiales.【F:AGI_Evolutive/autonomy/auto_signals.py†L153-L236】【F:AGI_Evolutive/autonomy/auto_signals.py†L212-L236】 |
| `signals[*].metadata` | mapping | Non | Stockée dans `AutoSignal.metadata` pour décrire la méthode de mesure (fenêtre, agrégat).【F:AGI_Evolutive/autonomy/auto_signals.py†L53-L88】【F:AGI_Evolutive/autonomy/auto_signals.py†L212-L223】 |
| `signals[*].last_value` | nombre | Non | Initialise `AutoSignal.last_value` pour guider immédiatement la mise en forme des récompenses.【F:AGI_Evolutive/autonomy/auto_signals.py†L212-L231】 |
| `signals[*].last_source` | `str` | Non | Conserve l’origine de l’observation (`llm`, `baseline`, etc.) dans la trace locale.【F:AGI_Evolutive/autonomy/auto_signals.py†L212-L233】 |
| `signals[*].last_updated` | timestamp float | Non | Par défaut à `time.time()` si absent ; permet de dater la dernière observation connue.【F:AGI_Evolutive/autonomy/auto_signals.py†L212-L231】 |

### `auto_signal_keywords` — `AGI_Evolutive/autonomy/auto_signals.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `keywords` | liste de `str` | Oui | Restituée telle quelle par `extract_keywords` pour fournir des indices aux modules amont (UI, intentions).【F:AGI_Evolutive/autonomy/auto_signals.py†L238-L258】 |
| `confidence` | nombre ∈ [0, 1] | Non | Propagé pour indiquer la fiabilité de l'extraction automatique.【F:AGI_Evolutive/autonomy/auto_signals.py†L238-L258】 |
| `notes` | `str` | Non | Conservé dans les journaux pour contextualiser l'extraction (ambiguïtés, risques).【F:AGI_Evolutive/autonomy/auto_signals.py†L238-L258】 |

## Auto-amélioration

### `code_evolver` — `AGI_Evolutive/self_improver/code_evolver.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Non | Journalisé pour contextualiser le lot de patches proposé.【F:AGI_Evolutive/self_improver/code_evolver.py†L214-L238】 |
| `patches` | liste de mappings | Oui | Chaque entrée est transformée en :class:`CodePatch` puis évaluée côté Python.【F:AGI_Evolutive/self_improver/code_evolver.py†L240-L276】【F:AGI_Evolutive/self_improver/code_evolver.py†L280-L300】 |
| `patches[*].target_id` | `str` | Oui | Permet d’associer la proposition à un fichier/module connu ; défaut sur la première cible valide.【F:AGI_Evolutive/self_improver/code_evolver.py†L252-L272】 |
| `patches[*].patched_source` | `str` non vide | Oui | Écrase directement la source locale lors de la promotion du patch.【F:AGI_Evolutive/self_improver/code_evolver.py†L92-L136】【F:AGI_Evolutive/self_improver/code_evolver.py†L308-L325】 |
| `patches[*].assessment.should_promote` | booléen | Oui | Conditionne la valeur `passed` utilisée par `SelfImprover.run_code_cycle` pour enregistrer un candidat.【F:AGI_Evolutive/self_improver/code_evolver.py†L121-L133】【F:AGI_Evolutive/self_improver/__init__.py†L153-L198】 |
| `patches[*].assessment.confidence` | nombre ∈ [0, 1] | Non | Propagé dans les logs et la mémoire pour suivre la confiance du modèle.【F:AGI_Evolutive/self_improver/code_evolver.py†L102-L133】【F:AGI_Evolutive/self_improver/__init__.py†L162-L198】 |
| `patches[*].evaluation.expected_metrics` | mapping | Non | Utilisé tel quel comme métriques projetées pour le staging de promotion.【F:AGI_Evolutive/self_improver/code_evolver.py†L137-L157】【F:AGI_Evolutive/self_improver/__init__.py†L166-L190】 |
| `patches[*].evaluation.quality` / `canary` | mapping | Non | Archivé dans les métadonnées du candidat afin de conserver le diagnostic LLM.【F:AGI_Evolutive/self_improver/code_evolver.py†L137-L157】【F:AGI_Evolutive/self_improver/__init__.py†L180-L194】 |
| `patches[*].notes` | `str` | Non | Propagée dans l’historique et la mémoire pour informer les opérateurs humains.【F:AGI_Evolutive/self_improver/code_evolver.py†L137-L157】【F:AGI_Evolutive/self_improver/__init__.py†L162-L198】 |

## Raisonnement

### `reasoning_episode` — `AGI_Evolutive/reasoning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` non vide | Oui | Archivé dans `ReasoningSystem.history` et injecté dans les journaux runtime.【F:AGI_Evolutive/reasoning/strategies.py†L350-L355】【F:AGI_Evolutive/reasoning/__init__.py†L127-L133】 |
| `confidence` / `final_confidence` | nombre ∈ [0, 1] | Oui | Clampé puis exposé comme `final_confidence` pour guider les calibrations aval.【F:AGI_Evolutive/reasoning/strategies.py†L366-L384】 |
| `hypothesis` | mapping | Oui | Normalisé et utilisé pour renseigner `chosen_hypothesis` afin d’assurer la compatibilité legacy.【F:AGI_Evolutive/reasoning/strategies.py†L291-L372】 |
| `proposals` | liste d’objets | Non | Chaque proposition est reconstruite (`label`, `summary`, `confidence`, `support`, `tests`, `actions`) avant diffusion.【F:AGI_Evolutive/reasoning/strategies.py†L211-L266】【F:AGI_Evolutive/reasoning/strategies.py†L355-L356】 |
| `tests` | liste d’objets ou de chaînes | Non | Convertis en mappings structurés et répliqués dans `tests_text` pour l’UI legacy.【F:AGI_Evolutive/reasoning/strategies.py†L298-L307】【F:AGI_Evolutive/reasoning/strategies.py†L374-L383】 |
| `questions` | liste (objets ou chaînes) | Non | Normalisées via `ReasoningQuestion` pour piloter les relances utilisateur.【F:AGI_Evolutive/reasoning/strategies.py†L309-L317】 |
| `actions` | liste d’objets | Non | Transformées en `ReasoningAction` (label/utility/priority/notes) afin d’orienter l’orchestrateur.【F:AGI_Evolutive/reasoning/strategies.py†L319-L327】【F:AGI_Evolutive/reasoning/strategies.py†L355-L358】 |
| `learning` | liste de `str` | Non | Restitué tel quel pour enrichir la mémoire métacognitive.【F:AGI_Evolutive/reasoning/strategies.py†L328-L361】 |
| `metadata` | mapping | Non | Fusionné dans la directive et conservé pour l’observabilité (`raw_llm_result`).【F:AGI_Evolutive/reasoning/strategies.py†L330-L365】 |
| `notes` | `str` | Non | Stocké tel quel et recopié dans les journaux de raisonnement.【F:AGI_Evolutive/reasoning/strategies.py†L329-L385】【F:AGI_Evolutive/reasoning/__init__.py†L127-L133】 |
| `cost` / `duration` | nombres | Non | Conservent le budget estimé du modèle pour l’instrumentation runtime.【F:AGI_Evolutive/reasoning/strategies.py†L331-L364】 |

Le `ReasoningSystem` assemble automatiquement le contexte (identité, intentions, état homeostatique, extraits mémoire, outils disponibles) avant d’appeler le contrat `reasoning_episode`, garantissant un unique aller-retour LLM pour l’ensemble du pipeline.【F:AGI_Evolutive/reasoning/__init__.py†L119-L178】【F:AGI_Evolutive/reasoning/__init__.py†L148-L226】

## Retrieval

### `retrieval_orchestrator` — `AGI_Evolutive/retrieval/adaptive_controller.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `plan_id` | `str` | Non | Identifiant de session stocké dans le contexte transmis aux couches amont.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L86-L137】 |
| `expansions` | liste de `str` | Non | Requêtes supplémentaires appliquées telles quelles au build de contexte planifié.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L90-L111】 |
| `overrides.retrieval` | mapping | Non | Fusionné avec la configuration de base pour ajuster densité/sparse et recency.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L113-L133】 |
| `overrides.guards` | mapping | Non | Alimente directement les garde-fous du pipeline (scores minimaux, refus).【F:AGI_Evolutive/retrieval/adaptive_controller.py†L113-L133】 |
| `overrides.rerank` / `overrides.compose` | mapping | Non | Transmis tels quels aux consommateurs pour contrôler rerank & composition.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L113-L133】 |
| `actions` | liste de mappings | Non | Notes structurées journalisées pour audit et supervision métacognitive.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L99-L107】 |
| `decision` | `str` | Non | Indique l’orientation globale (proceed/refine/refuse) exposée dans le contexte.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L99-L107】 |
| `notes` | liste de `str` | Non | Consignées telles quelles pour enrichir les logs et briefings opérés par l’orchestrateur.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L101-L107】 |
| `meta` | mapping | Non | Stocké pour garder la trace (confiance, signaux) de la décision de planification.【F:AGI_Evolutive/retrieval/adaptive_controller.py†L101-L107】 |

### `retrieval_answer` — `AGI_Evolutive/retrieval/rag5/pipeline.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `status` | `str` (`ok/refused/error`) | Oui | Conditionne la suite de traitement (diffusion ou message de refus).【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L122-L147】 |
| `answer` | `str` | Non | Message final renvoyé à l’utilisateur en cas de succès.【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L122-L147】 |
| `citations` | liste de mappings | Non | Chaque citation est stockée et réexposée (doc_id, extrait, confiance).【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L129-L140】 |
| `diagnostics` | mapping | Non | Inclut budgets/tokens/documents utilisés pour observabilité.【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L141-L147】 |
| `notes` | liste de `str` | Non | Fournit les recommandations complémentaires du LLM (moderation, follow-up).【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L122-L147】 |
| `meta` | mapping | Non | Conservé pour instrumentation additionnelle (scores, trace de raisonnement).【F:AGI_Evolutive/retrieval/rag5/pipeline.py†L141-L147】 |

## Mémoire

### `memory_store_strategy` — `AGI_Evolutive/memory/memory_store.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `normalized_kind` | `str` non vide | Non | Remplace le champ `kind` stocké si fourni.【F:AGI_Evolutive/memory/memory_store.py†L200-L208】 |
| `tags` | liste de `str` | Non | Fusionne les étiquettes proposées avec celles présentes, sans doublon.【F:AGI_Evolutive/memory/memory_store.py†L209-L215】 |
| `metadata_updates` | mapping clé/valeur sérialisable | Non | Applique une mise à jour directe sur `metadata` avant indexation.【F:AGI_Evolutive/memory/memory_store.py†L216-L218】 |
| `retention_priority` | `str` | Non | Enregistre la recommandation dans `metadata.retention_priority`.【F:AGI_Evolutive/memory/memory_store.py†L219-L222】 |
| `notes` | libre (stocké tel quel) | Non | Ajoute l’élément à `metadata.llm_notes` si la liste existe.【F:AGI_Evolutive/memory/memory_store.py†L223-L227】 |

**Erreurs courantes** : répondre avec des tags non textuels ou des métadonnées non sérialisables
(la mise à jour est ignorée) ; oublier que `notes` est empilé dans une liste, donc éviter les
blocs massifs.

### `memory_retrieval_ranking` — `AGI_Evolutive/memory/retrieval.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `rankings` | liste d’objets | Oui | Chaque entrée est parcourue pour ajuster les scores et le rang final.【F:AGI_Evolutive/memory/retrieval.py†L357-L419】 |
| `rankings[*].id` | identifiant numérique existant | Oui | Permet d’associer l’ajustement au candidat source.【F:AGI_Evolutive/memory/retrieval.py†L383-L407】 |
| `rankings[*].adjusted_score` ou `score` | nombre | Oui | Sert de score LLM mixé à 35 % dans la note finale.【F:AGI_Evolutive/memory/retrieval.py†L389-L420】 |
| `rankings[*].rationale`/`reason` | `str` | Non | Copié dans `llm_rationale` pour la traçabilité.【F:AGI_Evolutive/memory/retrieval.py†L395-L417】 |
| `rankings[*].priority` | valeur libre | Non | Repris tel quel pour enrichir le candidat.【F:AGI_Evolutive/memory/retrieval.py†L395-L419】 |
| `rankings[*].rank` | entier | Non | Définit l’ordre final si fourni, sinon ordre d’itération.【F:AGI_Evolutive/memory/retrieval.py†L394-L419】 |

**Vigilance** : toute entrée dont `id` ne correspond à aucun candidat est ignorée. Éviter les ids
texte, ils ne sont pas convertis.

### `memory_summarizer` — `AGI_Evolutive/memory/summarizer.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `digests` | liste d’objets | Oui | Chaque entrée est persistée via `add_item` et remplace l’ancien pipeline heuristique.【F:AGI_Evolutive/memory/summarizer.py†L250-L295】 |
| `digests[*].reference` | `str` | Oui | Stocké dans `metadata.llm_reference` et utilisé pour tracer la compression.【F:AGI_Evolutive/memory/summarizer.py†L260-L291】 |
| `digests[*].level` | `str` | Oui | Devient le champ `kind` du digest persistant.【F:AGI_Evolutive/memory/summarizer.py†L263-L291】 |
| `digests[*].summary` | `str` | Oui | Corps textuel du digest sauvegardé.【F:AGI_Evolutive/memory/summarizer.py†L263-L291】 |
| `digests[*].source_ids` | liste de `str` | Non | Recopiée dans `lineage` pour garder les liens aux souvenirs sources.【F:AGI_Evolutive/memory/summarizer.py†L285-L291】 |
| `digests[*].compress_ids` | liste de `str` | Non | Permet d’annoter les souvenirs compressés (`compressed_into`).【F:AGI_Evolutive/memory/summarizer.py†L297-L306】 |
| `digests[*].key_points` | liste | Non | Stockée dans `metadata.key_points` pour l’UI ou l’audit.【F:AGI_Evolutive/memory/summarizer.py†L271-L291】 |
| `follow_up` | liste de `str` | Non | Propagée dans `SummarizationResult.follow_up` pour pilotage métier.【F:AGI_Evolutive/memory/summarizer.py†L222-L245】 |
| `notes` | `str` | Non | Conserve des instructions libres pour les opérateurs.【F:AGI_Evolutive/memory/summarizer.py†L240-L245】 |

**Vigilance** : fournir des `reference` stables afin d’éviter les doublons lors des appels successifs.

### `semantic_memory_maintenance` — `AGI_Evolutive/memory/semantic_memory_manager.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `run_concepts` | booléen | Oui | Déclenche ou non l’appel au module d’extraction de concepts.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L103-L121】 |
| `concept_batch` | entier | Non | Taille maximale du lot envoyé à `ConceptExtractor.run_once`.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L113-L118】 |
| `run_summaries` | booléen | Oui | Autorise la génération de digests via `ProgressiveSummarizer.step`.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L115-L118】 |
| `summary_limit` | entier | Non | Transmis en limite au résumeur LLM.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L116-L118】 |
| `rationale` | `str` | Non | Conserve la justification du plan pour la télémétrie.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L70-L86】 |
| `follow_up` | liste de `str` | Non | Passée telle quelle aux opérateurs humains ou à d’autres modules.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L70-L86】 |

**Vigilance** : le plan est exécuté tel quel, sans heuristique de repli ; un `run_concepts=False` n’effectuera aucun traitement même si un backlog persiste.

### `memory_system_narrative` — `AGI_Evolutive/memory/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `enhanced_narrative` | `str` | Non | Stocké dans `llm_enhanced_narrative` pour remplacer le récit de base.【F:AGI_Evolutive/memory/__init__.py†L1787-L1809】 |
| `coherence` | nombre | Non | Écrase la cohérence calculée s’il est convertible en flottant.【F:AGI_Evolutive/memory/__init__.py†L1809-L1813】 |
| `insights` | liste | Non | Recopiée en tant qu’`llm_insights` pour archivage.【F:AGI_Evolutive/memory/__init__.py†L1814-L1817】 |
| `notes` | libre | Non | Stocké dans `llm_notes` (utilisé pour débogage).【F:AGI_Evolutive/memory/__init__.py†L1816-L1818】 |

**Conseil** : respecter les identifiants d’événements passés dans le payload pour rester
autobiographique.

### `memory_long_term_digest` — `AGI_Evolutive/memory/alltime.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| _toute réponse_ | mapping sérialisable | Non | Copié tel quel dans `details.llm_analysis` et persistant sur disque.【F:AGI_Evolutive/memory/alltime.py†L271-L305】 |

**Vigilance** : ne renvoyer que des structures JSON-compatibles (pas d’objets Python). Le digest
rejoue ces données dans les exports analytiques.

### `memory_concept_curation` — `AGI_Evolutive/memory/concept_store.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `concepts` | liste d’objets (`label`, `salience`, `confidence`, `evidence`, `source_ids`) | Oui | Chaque entrée est fusionnée via `_upsert_concept` pour mettre à jour le graphe normalisé.【F:AGI_Evolutive/memory/concept_store.py†L74-L122】 |
| `relations` | liste d’objets (`subject`, `verb`, `object`, `confidence`, `evidence`) | Non | Injectées via `_upsert_relation` afin de conserver la structure relationnelle à jour.【F:AGI_Evolutive/memory/concept_store.py†L124-L160】 |
| `highlights`/`notes` | liste de chaînes | Non | Répercutées dans `ConceptExtractionResult` puis archivées dans les métadonnées du store.【F:AGI_Evolutive/memory/concept_extractor.py†L142-L180】【F:AGI_Evolutive/memory/concept_store.py†L49-L58】 |

**Vigilance** : les labels sont normalisés (`lower()`) avant fusion ; utilisez des libellés stables pour éviter les doublons.

### `memory_index_optimizer` — `AGI_Evolutive/memory/indexing.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `reranked` | liste d’objets | Non | Décrit les boosts à appliquer sur les documents retournés.【F:AGI_Evolutive/memory/indexing.py†L188-L229】 |
| `reranked[*].id` | identifiant numérique | Oui (par boost) | Localise le document concerné ; sinon l’ajustement est ignoré.【F:AGI_Evolutive/memory/indexing.py†L211-L220】 |
| `reranked[*].boost` | nombre | Non | Ajuste le score final si fourni.【F:AGI_Evolutive/memory/indexing.py†L222-L224】 |
| `reranked[*].justification` | `str` | Non | Ajouté dans `llm_justifications` pour la trace opérateur.【F:AGI_Evolutive/memory/indexing.py†L224-L228】 |

### `memory_semantic_bridge` — `AGI_Evolutive/memory/semantic_bridge.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `memories` | liste d’objets (id/kind/text/tags/salience) | Oui | Relais direct vers le `SemanticMemoryManager`; les IDs doivent rester intacts.【F:AGI_Evolutive/memory/semantic_bridge.py†L96-L118】 |
| autres champs | sérialisable | Non | Relayés tels quels au manager si présents.【F:AGI_Evolutive/memory/semantic_bridge.py†L108-L116】 |

**Vigilance** : le manager se base sur `id` pour consigner les annotations ; toute perte d’identifiant
rend l’annotation inutilisable.

### `semantic_memory_manager` — `AGI_Evolutive/memory/semantic_memory_manager.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `tasks` | liste d’objets | Oui | Chaque entrée ajuste périodicité et prochaine exécution d’une tâche connue.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L361-L418】 |
| `tasks[*].task` | alias reconnu | Oui | Doit correspondre à une tâche enregistrée, sinon l’entrée est ignorée.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L389-L405】 |
| `tasks[*].category` | `str` (`urgent`, `court_terme`, `long_terme`, …) | Oui | Détermine la stratégie d’ajustement des périodes.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L403-L417】 |
| `tasks[*].period`/`next_run` | nombres | Non | Valeurs recalculées à partir de la catégorie ; reprises dans l’historique si présentes.【F:AGI_Evolutive/memory/semantic_memory_manager.py†L401-L418】 |

**Vigilance** : passer des tâches inconnues laisse la guidance vide ; toujours réemployer les alias
renvoyés dans le payload entrant.

## Langage

### `dialogue_state` — `AGI_Evolutive/language/dialogue_state.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `state_summary`/`summary` | `str` | Oui | Alimentent la synthèse courante du dialogue.【F:AGI_Evolutive/language/dialogue_state.py†L123-L138】 |
| `open_commitments` | liste | Oui | Remplace la liste d’engagements suivis ; utiliser le même schéma que l’entrée.【F:AGI_Evolutive/language/dialogue_state.py†L125-L129】 |
| `pending_questions` | liste | Oui | S’injecte dans la file locale ; une omission vide la liste courante.【F:AGI_Evolutive/language/dialogue_state.py†L125-L129】 |
| `notes` | `str` | Non | Ajoutées si non vides pour contextualiser l’état.【F:AGI_Evolutive/language/dialogue_state.py†L129-L132】 |

### `language_nlg` — `AGI_Evolutive/language/nlg.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `message` | `str` | Oui | Deviens la réponse finale stockée dans `NLGContext.text` (fallback sur le texte de base si vide).【F:AGI_Evolutive/language/nlg.py†L111-L134】 |
| `sections` | liste de mappings | Non | Copiée dans `NLGContext.sections` et sert à reconstruire le message si nécessaire.【F:AGI_Evolutive/language/nlg.py†L70-L101】【F:AGI_Evolutive/language/nlg.py†L192-L205】 |
| `sections[*].name` | `str` | Non | Conservé tel quel dans la sortie brute pour diagnostic.【F:AGI_Evolutive/language/nlg.py†L70-L93】 |
| `sections[*].text` | `str` | Non | Texte de la section ; ignoré si vide.【F:AGI_Evolutive/language/nlg.py†L87-L93】 |
| `applied_actions` | liste de mappings | Non | Remplace `NLGContext.actions` pour exposer les décisions du modèle.【F:AGI_Evolutive/language/nlg.py†L97-L101】【F:AGI_Evolutive/language/nlg.py†L214-L219】 |
| `tone` | `str` | Non | Ajouté à `NLGContext.meta` et accessible aux couches aval.【F:AGI_Evolutive/language/nlg.py†L105-L115】 |
| `safety_notes` | liste de `str` | Non | Archivées dans `NLGContext.meta` sous forme normalisée.【F:AGI_Evolutive/language/nlg.py†L107-L109】【F:AGI_Evolutive/language/nlg.py†L214-L219】 |
| `meta` | mapping | Non | Fusionné directement dans `NLGContext.meta`.【F:AGI_Evolutive/language/nlg.py†L105-L115】【F:AGI_Evolutive/language/nlg.py†L214-L219】 |

**Remarque** : en l'absence de `message`, les sections sont concaténées ; si toutes sont vides, le texte
initial est conservé.【F:AGI_Evolutive/language/nlg.py†L95-L103】

## Mémoire épisodique

### `episodic_linker` — `AGI_Evolutive/memory/episodic_linker.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `links` | liste d’objets | Non | Ajoute des relations supplémentaires entre souvenirs si valides.【F:AGI_Evolutive/memory/episodic_linker.py†L553-L615】 |
| `links[*].from`/`src` | alias fourni (`m0`, `m1`, …) ou id existant | Oui (par lien) | Converti via `alias_map` vers l’identifiant réel.【F:AGI_Evolutive/memory/episodic_linker.py†L585-L607】 |
| `links[*].to`/`dst` | alias/id | Oui | Identique à `from` ; rejeté si introuvable.【F:AGI_Evolutive/memory/episodic_linker.py†L585-L607】 |
| `links[*].type_lien`/`relation` | `str` | Oui | Converti via `LLM_RELATION_MAP` vers `CAUSES`, `SUPPORTS`, etc.【F:AGI_Evolutive/memory/episodic_linker.py†L588-L609】 |
| `links[*].confidence` | nombre ∈ [0, 1] | Non | Conservé si convertible ; sinon omis.【F:AGI_Evolutive/memory/episodic_linker.py†L607-L614】 |
| `notes` | `str` | Non | Archivé avec les liens générés pour inspection.【F:AGI_Evolutive/memory/episodic_linker.py†L613-L617】 |

**Conseil** : rester fidèle aux alias fournis (`m0`, `m1`…) décrivant les expériences internes au
lieu de réintroduire des intitulés techniques obsolètes.

## Identité & cognition

### `homeostasis` — `AGI_Evolutive/cognition/homeostasis.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `drive_targets` | mapping | Non | Chaque valeur clampée ∈ [0,1] écrase les drives internes correspondants.【F:AGI_Evolutive/cognition/homeostasis.py†L109-L149】【F:AGI_Evolutive/cognition/homeostasis.py†L179-L204】 |
| `rewards` | mapping | Non | Met à jour `intrinsic_reward`, `extrinsic_reward`, `hedonic_reward` et le bloc `state["rewards"]`.【F:AGI_Evolutive/cognition/homeostasis.py†L150-L170】 |
| `actions` | liste de mappings | Non | Stockées dans `state["meta"]["actions"]` et remontées aux modules de supervision.【F:AGI_Evolutive/cognition/homeostasis.py†L171-L186】 |
| `notes`/`advisories` | liste de `str` | Non | Normalisées et archivées dans `state["meta"]["advisories"]` pour inspection.【F:AGI_Evolutive/cognition/homeostasis.py†L171-L186】 |
| `telemetry` | mapping | Non | Fusionné dans `state["meta"]["telemetry"]` pour audit.【F:AGI_Evolutive/cognition/homeostasis.py†L171-L186】 |

**Conseil** : retourner des drives absolus (`drive_targets`) plutôt que des deltas ; la classe applique directement la valeur issue du LLM.

### `identity_mission` — `AGI_Evolutive/cognition/identity_mission.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `mission` | mapping | Oui | Les clés fournies (ex. `prioritaire`, `support`, `vision`) remplacent directement la mission persistée.【F:AGI_Evolutive/cognition/identity_mission.py†L22-L61】【F:AGI_Evolutive/cognition/identity_mission.py†L126-L157】 |
| `mission_text`/`mission_statement` | `str` | Non | Si non vide, stocké comme synthèse textuelle de la mission et utilisé pour le reporting.【F:AGI_Evolutive/cognition/identity_mission.py†L38-L41】【F:AGI_Evolutive/cognition/identity_mission.py†L138-L142】 |
| `priorities` | liste de mappings | Non | Chaque entrée normalisée est enregistrée pour guider les focus futurs (`label`, `horizon`, `rationale`).【F:AGI_Evolutive/utils/llm_contracts.py†L125-L146】【F:AGI_Evolutive/cognition/identity_mission.py†L142-L149】 |
| `follow_up` | liste de mappings | Non | Actions complémentaires (ex. `request_confirmation`) déclenchent des notifications et sont archivées.【F:AGI_Evolutive/utils/llm_contracts.py†L148-L165】【F:AGI_Evolutive/orchestrator.py†L2470-L2488】 |
| `notes` | liste de `str` | Non | Journalisées avec horodatage pour suivi interne.【F:AGI_Evolutive/utils/llm_contracts.py†L167-L178】【F:AGI_Evolutive/cognition/identity_mission.py†L131-L142】 |
| `telemetry` | mapping | Non | Fusionné tel quel dans l’état pour audit ou dashboards.【F:AGI_Evolutive/utils/llm_contracts.py†L180-L186】【F:AGI_Evolutive/cognition/identity_mission.py†L146-L154】 |

**Conseil** : profiter de `follow_up` pour signaler explicitement les validations humaines nécessaires plutôt que d’encoder des seuils implicites.

### `cognition_proposer` — `AGI_Evolutive/cognition/proposer.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `suggestions` | liste d’objets | Non | Remplace la liste de propositions heuristiques si fournie.【F:AGI_Evolutive/cognition/proposer.py†L35-L64】 |
| `suggestions[*].type` | `str` | Oui (par suggestion) | Définit le type d’opération (`update`, `add`, …).【F:AGI_Evolutive/cognition/proposer.py†L55-L58】 |
| `suggestions[*].path`/`target` | liste/chemin | Oui | Sert à appliquer la proposition dans le self-model.【F:AGI_Evolutive/cognition/proposer.py†L55-L58】 |
| `suggestions[*].value`/`adjustment` | valeur sérialisable | Oui | Appliquée telle quelle lors de l’intégration.【F:AGI_Evolutive/cognition/proposer.py†L55-L58】 |
| `suggestions[*].cause` | `str` | Non | Documente la justification de la proposition.【F:AGI_Evolutive/cognition/proposer.py†L55-L60】 |
| `notes` | `str` | Non | Ajoutée comme proposition de type `note` pour archivage.【F:AGI_Evolutive/cognition/proposer.py†L64-L66】 |

### `cognition_context_inference` — `AGI_Evolutive/cognition/context_inference.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `where` | mapping | Non | Si `should_update` est vrai, appliqué directement au self-model (`identity.where`).【F:AGI_Evolutive/cognition/context_inference.py†L119-L151】【F:AGI_Evolutive/cognition/context_inference.py†L165-L188】 |
| `should_update` | booléen | Oui | Détermine si l’agent applique la mise à jour du "where" à l’identité persistée.【F:AGI_Evolutive/cognition/context_inference.py†L137-L151】 |
| `confidence` | nombre ∈ [0, 1] | Non | Journalisé avec la directive pour diagnostic et suivi.【F:AGI_Evolutive/cognition/context_inference.py†L137-L147】【F:AGI_Evolutive/cognition/context_inference.py†L178-L188】 |
| `actions` | liste de `str` | Non | Restituées à l’orchestrateur pour déclencher des suivis manuels éventuels.【F:AGI_Evolutive/cognition/context_inference.py†L137-L147】【F:AGI_Evolutive/cognition/context_inference.py†L178-L188】 |
| `notes` | liste de `str` | Non | Journalisées dans `arch._where_last` pour audit interne.【F:AGI_Evolutive/cognition/context_inference.py†L137-L147】【F:AGI_Evolutive/cognition/context_inference.py†L178-L188】 |
| `telemetry` | mapping | Non | Fusionné dans l’historique `arch._where_last` pour inspection ultérieure.【F:AGI_Evolutive/cognition/context_inference.py†L137-L147】【F:AGI_Evolutive/cognition/context_inference.py†L178-L188】 |

### `cognition_goal_prioritizer` — `AGI_Evolutive/cognition/prioritizer.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `priorities` | liste d’objets | Oui | Remplace intégralement la priorisation du planner en appliquant `priority`, `tags`, `status` et `metadata` sur chaque plan ciblé.【F:AGI_Evolutive/cognition/prioritizer.py†L209-L251】【F:AGI_Evolutive/cognition/prioritizer.py†L285-L309】 |
| `priorities[*].goal_id` | `str` | Oui (par entrée) | Sert à retrouver le plan dans l’état du planner avant application.【F:AGI_Evolutive/cognition/prioritizer.py†L173-L205】【F:AGI_Evolutive/cognition/prioritizer.py†L285-L309】 |
| `priorities[*].priority` | nombre ∈ [0, 1] | Oui | Injecté tel quel dans `plan["priority"]` après clamp.【F:AGI_Evolutive/cognition/prioritizer.py†L138-L170】【F:AGI_Evolutive/cognition/prioritizer.py†L209-L251】 |
| `priorities[*].tags` | liste | Non | Remplace la liste de tags du plan pour refléter la décision LLM.【F:AGI_Evolutive/cognition/prioritizer.py†L141-L168】【F:AGI_Evolutive/cognition/prioritizer.py†L209-L230】 |
| `priorities[*].status` | `str` | Non | Permet de suspendre/reprendre un plan directement via la réponse LLM.【F:AGI_Evolutive/cognition/prioritizer.py†L148-L170】【F:AGI_Evolutive/cognition/prioritizer.py†L209-L230】 |
| `priorities[*].notes` | liste de `str` | Non | Ajoutées dans `plan["priority_notes"]` pour la traçabilité des décisions.【F:AGI_Evolutive/cognition/prioritizer.py†L142-L170】【F:AGI_Evolutive/cognition/prioritizer.py†L209-L230】 |
| `priorities[*].metadata` | mapping | Non | Fusionné dans `plan["llm_priority"]` afin de partager des signaux additionnels.【F:AGI_Evolutive/cognition/prioritizer.py†L144-L170】【F:AGI_Evolutive/cognition/prioritizer.py†L209-L230】 |
| `summary` | `str` | Non | Journalisé dans les traces de priorisation pour contextualiser la décision globale.【F:AGI_Evolutive/cognition/prioritizer.py†L253-L309】 |
| `global_notes` | liste | Non | Exposées dans les logs de l’architecture pour suivi opérateur.【F:AGI_Evolutive/cognition/prioritizer.py†L253-L309】 |

### `planner_support` — `AGI_Evolutive/cognition/planner.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Non | Stocké tel quel pour contextualiser le plan courant.【F:AGI_Evolutive/cognition/planner.py†L166-L175】【F:AGI_Evolutive/cognition/planner.py†L195-L213】 |
| `plan` | liste d’objets | Oui | Normalisée en étapes `PlannerStep` et persistée dans l’état interne.【F:AGI_Evolutive/cognition/planner.py†L126-L175】【F:AGI_Evolutive/cognition/planner.py†L195-L213】 |
| `plan[*].description` | `str` non vide | Oui | Sert de texte principal pour l’étape créée.【F:AGI_Evolutive/cognition/planner.py†L132-L148】 |
| `plan[*].id` | `str` | Non | Repris tel quel sinon généré sous la forme `llm_step_n`.【F:AGI_Evolutive/cognition/planner.py†L138-L143】 |
| `plan[*].priority` | nombre ∈ [0, 1] | Non | Clampé puis stocké pour l’arbitrage.【F:AGI_Evolutive/cognition/planner.py†L144-L146】【F:AGI_Evolutive/cognition/planner.py†L157-L163】 |
| `plan[*].depends_on` | liste de `str` | Non | Nettoyée et conservée pour piloter les dépendances.【F:AGI_Evolutive/cognition/planner.py†L143-L145】【F:AGI_Evolutive/cognition/planner.py†L208-L209】 |
| `plan[*].action_type` | `str` | Non | Définit `action.type` pour l’étape correspondante.【F:AGI_Evolutive/cognition/planner.py†L145-L146】【F:AGI_Evolutive/cognition/planner.py†L157-L163】 |
| `plan[*].notes` | liste de `str` | Non | Conservée dans l’étape et exposée aux consommateurs.【F:AGI_Evolutive/cognition/planner.py†L146-L147】【F:AGI_Evolutive/cognition/planner.py†L157-L163】 |
| `plan[*].metadata` | mapping | Non | Archivé tel quel dans l’étape normalisée.【F:AGI_Evolutive/cognition/planner.py†L147-L148】【F:AGI_Evolutive/cognition/planner.py†L157-L163】 |
| `risks` | liste de chaînes | Non | Stockée pour documentation et transmise dans le frame.【F:AGI_Evolutive/cognition/planner.py†L166-L175】【F:AGI_Evolutive/cognition/planner.py†L211-L213】 |
| `notes` | liste de chaînes | Non | Même traitement que `risks`, exposé dans le frame.【F:AGI_Evolutive/cognition/planner.py†L166-L175】【F:AGI_Evolutive/cognition/planner.py†L211-L213】 |

### `trigger_router` — `AGI_Evolutive/cognition/trigger_router.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `pipelines` | liste de `str` | Non | Définit l’ordre de priorité des pipelines ; le premier est choisi.【F:AGI_Evolutive/cognition/trigger_router.py†L37-L57】 |
| `secondary` | liste de `str` | Non | Consigné pour bascule ultérieure.【F:AGI_Evolutive/cognition/trigger_router.py†L37-L64】 |
| `notes` | `str` | Non | Journalisé pour expliquer la décision du routeur.【F:AGI_Evolutive/cognition/trigger_router.py†L43-L64】 |

## Objectifs

### `goal_interpreter` — `AGI_Evolutive/goals/heuristics.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `candidate_actions` | liste d’objets | Oui | Génère la file d’actions dérivée du but courant.【F:AGI_Evolutive/goals/heuristics.py†L120-L152】 |
| `candidate_actions[*].action` | `str` | Oui | Devient `type` de l’action ajoutée à la deque.【F:AGI_Evolutive/goals/heuristics.py†L132-L147】 |
| `candidate_actions[*].rationale` | `str` | Non | Copiée dans le payload d’action pour la traçabilité.【F:AGI_Evolutive/goals/heuristics.py†L138-L145】 |
| `normalized_goal` | `str` | Non | Stocké dans chaque action créée pour contextualiser le but.【F:AGI_Evolutive/goals/heuristics.py†L128-L143】 |
| `notes` | `str` | Non | Injecté dans la première action générée.【F:AGI_Evolutive/goals/heuristics.py†L145-L147】 |

### `goal_priority_review` — `AGI_Evolutive/goals/dag_store.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `priority` | nombre ∈ [0, 1] | Oui (sauf usage de `priority_delta`) | Recalcule la priorité du nœud, clampée entre 0 et 1.【F:AGI_Evolutive/goals/dag_store.py†L206-L236】 |
| `priority_delta` | nombre | Oui (alternative) | Ajoute un delta au fallback si `priority` absent.【F:AGI_Evolutive/goals/dag_store.py†L224-L236】 |
| `confidence` | nombre ∈ [0, 1] | Non | Pondère le mélange entre fallback et suggestion LLM.【F:AGI_Evolutive/goals/dag_store.py†L232-L236】 |

**Vigilance** : si ni `priority` ni `priority_delta` ne sont fournis, la revue est purement ignorée.

## Interaction & questionnement

### `question_manager` — `AGI_Evolutive/core/question_manager.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `questions` | liste d’objets | Oui | Chaque élément validé alimente la banque et la file d’attente.【F:AGI_Evolutive/core/question_manager.py†L344-L377】 |
| `questions[*].text` | `str` non vide | Oui | Question réellement poussée ; les doublons sont filtrés ensuite.【F:AGI_Evolutive/core/question_manager.py†L360-L377】 |
| autres champs (`insights`, `meta`, …) | sérialisable | Non | Repris tels quels si conformes au format courant.【F:AGI_Evolutive/core/question_manager.py†L344-L377】 |

### `question_auto_answer` — `AGI_Evolutive/core/question_manager.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `answer`/`text` | `str` non vide | Oui | Crée une suggestion d’auto-réponse avec source `llm`.【F:AGI_Evolutive/core/question_manager.py†L728-L754】 |
| `confidence` | nombre | Non | Clampé puis enregistré pour décider de l’auto-validation.【F:AGI_Evolutive/core/question_manager.py†L749-L756】 |
| `concepts`/`keywords`/`insights` | liste | Non | Nettoyés et ajoutés au rapport de réponse.【F:AGI_Evolutive/core/question_manager.py†L756-L767】 |
| `notes` | `str` | Non | Ajoutés en champ libre dans la suggestion.【F:AGI_Evolutive/core/question_manager.py†L767-L769】 |

## Action

### `action_interface` — `AGI_Evolutive/io/action_interface.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `actions` | liste d’objets | Oui | Liste évaluée ; chaque élément remplace ou complète l’estimation heuristique.【F:AGI_Evolutive/io/action_interface.py†L540-L590】 |
| `actions[*].name` | `str` | Oui | Sert d’étiquette d’action (fallback si absent).【F:AGI_Evolutive/io/action_interface.py†L552-L566】 |
| `actions[*].type` | `str` | Oui | Identifie la catégorie d’action pour le moteur d’exécution.【F:AGI_Evolutive/io/action_interface.py†L552-L566】 |
| `actions[*].impact`/`effort`/`risk` | nombres ∈ [0, 1] | Non | Clampés puis arrondis à trois décimales avant restitution.【F:AGI_Evolutive/io/action_interface.py†L566-L589】 |
| `actions[*].rationale` | `str` | Non | Remplace la justification heuristique si fournie.【F:AGI_Evolutive/io/action_interface.py†L552-L589】 |
| `notes` | `str` | Non | Ajoutées au rapport final pour guider l’opérateur.【F:AGI_Evolutive/io/action_interface.py†L571-L589】 |

**Astuces de revue**
- Vérifie systématiquement que les identifiants (`id`, alias LLM, chemins `path`) proviennent bien du
payload d’entrée.
- Les valeurs non sérialisables (objets Python, `set`, etc.) sont silencieusement écartées ; rester sur
un sous-ensemble JSON.
- Les champs indiqués « obligatoires » peuvent désactiver tout le bénéfice de l’appel si absents :
un test rapide via mocks LLM permet de s’en assurer avant déploiement.

## Learning

### `experiential_learning_cycle` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Oui | Journalise la synthèse de l’épisode dans l’historique interne du module.【F:AGI_Evolutive/learning/__init__.py†L87-L114】 |
| `confidence` | `float` ∈ [0, 1] | Oui | Sert de métrique principale pour le suivi méta-apprentissage.【F:AGI_Evolutive/learning/__init__.py†L87-L114】 |
| `actions` | liste d’objets | Non | Injectées telles quelles dans `LearningEpisodeOutcome.actions` pour orchestration future.【F:AGI_Evolutive/learning/__init__.py†L96-L110】 |
| `memory_updates` | liste d’objets | Non | Chaque élément est transmis aux stores mémoire via la couche appelante.【F:AGI_Evolutive/learning/__init__.py†L111-L114】 |
| `metrics` | `dict` | Non | Agrégées pour la persistance dans `to_state()`.【F:AGI_Evolutive/learning/__init__.py†L115-L118】 |
| `notes` | liste de `str` | Non | Ajoutées aux traces diagnostiques ; aucune interprétation automatique.【F:AGI_Evolutive/learning/__init__.py†L119-L122】 |

### `learning_self_assessment` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `concept` | `str` | Non | Recopié pour audit ; le module conserve la valeur initiale si absent.【F:AGI_Evolutive/learning/__init__.py†L150-L170】 |
| `confidence` | `float` ∈ [0, 1] | Oui | Valeur renvoyée directement aux gardes qualité pour la promotion auto.【F:AGI_Evolutive/learning/__init__.py†L164-L170】 |
| `coverage` | `dict` (`definition`/`examples`/`counterexample`) | Non | Stocké pour inspection et indicateurs méta.【F:AGI_Evolutive/learning/__init__.py†L164-L170】 |
| `evidence` | liste de `str` | Non | Conservée dans `last_self_assessment` pour faciliter les vérifications humaines.【F:AGI_Evolutive/learning/__init__.py†L164-L170】 |
| `notes` | liste de `str` | Non | Ajoutées à l’historique des décisions.【F:AGI_Evolutive/learning/__init__.py†L164-L170】 |

### `learning_auto_curriculum` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `curriculum_entry` | `dict` | Oui | Consigné dans `_curriculum_log` et utilisé pour guider les auto-évolutions futures.【F:AGI_Evolutive/learning/__init__.py†L172-L191】 |
| `adjustments` | `dict` | Non | Valeurs appliquées côté appelant (ex. mise à jour de momentum).【F:AGI_Evolutive/learning/__init__.py†L182-L191】 |
| `notes` | liste de `str` | Non | Journalisées pour audit humain.【F:AGI_Evolutive/learning/__init__.py†L184-L191】 |

### `learning_meta_controller` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `module` | `str` | Oui | Identifie le module concerné par le feedback ; conservé dans `_feedback_log`.【F:AGI_Evolutive/learning/__init__.py†L210-L236】 |
| `adjustments` | `dict` | Oui | Objet principal appliqué par les couches supérieures (ex. nouveau learning rate).【F:AGI_Evolutive/learning/__init__.py†L222-L236】 |
| `alerts` | liste de `str` | Non | Déclenchent des notifications méta si présentes.【F:AGI_Evolutive/learning/__init__.py†L225-L236】 |
| `notes` | liste de `str` | Non | Ajoutées à l’historique pour expliquer les choix.【F:AGI_Evolutive/learning/__init__.py†L232-L236】 |

### `learning_curriculum_planner` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `focus_modules` | liste de `str` | Oui | Ordonne les priorités transmises au scheduling d’apprentissage.【F:AGI_Evolutive/learning/__init__.py†L238-L262】 |
| `recommendations` | liste d’objets | Non | Chaque recommandation est loggée pour suivi ; libre d’interprétation côté opérateur.【F:AGI_Evolutive/learning/__init__.py†L244-L262】 |
| `review_after` | `int` (minutes) | Non | Sert de suggestion pour replanifier le curriculum.【F:AGI_Evolutive/learning/__init__.py†L248-L262】 |
| `notes` | liste de `str` | Non | Trace textuelle du raisonnement du modèle.【F:AGI_Evolutive/learning/__init__.py†L244-L262】 |

### `learning_transfer_mapping` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Oui | Ajouté dans `_transfer_log` pour audit des transferts.【F:AGI_Evolutive/learning/__init__.py†L282-L312】 |
| `transferred_items` | liste de `str` | Non | Documente les éléments réellement migrés.【F:AGI_Evolutive/learning/__init__.py†L286-L312】 |
| `difficulties` | liste de `str` | Non | Aide à cibler les lacunes lors du prochain cycle.【F:AGI_Evolutive/learning/__init__.py†L286-L312】 |
| `success_score` | `float` ∈ [0, 1] | Oui | Base pour les métriques méta et l’acceptation du transfert.【F:AGI_Evolutive/learning/__init__.py†L288-L312】 |
| `updated_target` | `dict` | Non | Si présent, remplace l’état local du domaine cible.【F:AGI_Evolutive/learning/__init__.py†L293-L312】 |
| `notes` | liste de `str` | Non | Conservées dans le log pour compréhension future.【F:AGI_Evolutive/learning/__init__.py†L286-L312】 |

### `learning_reinforcement_policy` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `action` | `str` | Oui | Action exécutée ou utilisée comme fallback si la liste d’entrée était vide.【F:AGI_Evolutive/learning/__init__.py†L330-L362】 |
| `estimated_value` | `float` | Oui | Restitué par `update_value` pour compatibilité avec l’API héritée.【F:AGI_Evolutive/learning/__init__.py†L354-L362】 |
| `confidence` | `float` ∈ [0, 1] | Non | Permet d’arbitrer avec d’autres politiques si nécessaire.【F:AGI_Evolutive/learning/__init__.py†L343-L352】 |
| `policy_notes` | liste de `str` | Non | Journalisées dans `_policy_log` pour inspection.【F:AGI_Evolutive/learning/__init__.py†L343-L352】 |

### `learning_curiosity_update` — `AGI_Evolutive/learning/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `reward` | `float` ∈ [-1, 1] | Oui | Valeur de retour directe de `CuriosityEngine.stimulate`.【F:AGI_Evolutive/learning/__init__.py†L364-L399】 |
| `curiosity_level` | `float` ∈ [0, 1] | Oui | Met à jour le niveau interne pour les appels futurs.【F:AGI_Evolutive/learning/__init__.py†L390-L399】 |
| `signals` | liste de `str` | Non | Permet d’informer les autres systèmes (motivation, métacognition).【F:AGI_Evolutive/learning/__init__.py†L384-L399】 |
| `notes` | liste de `str` | Non | Trace les heuristiques ou doutes du modèle.【F:AGI_Evolutive/learning/__init__.py†L384-L399】 |

## Runtime

### `jsonl_logger` — `AGI_Evolutive/runtime/logger.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Non | Journalisé dans `llm_analysis.summary` pour contextualiser chaque événement.【F:AGI_Evolutive/runtime/logger.py†L37-L55】 |
| `tags` | liste de `str` | Non | Fusionnés avec `extra_tags` puis persistés dans l'enregistrement JSONL.【F:AGI_Evolutive/runtime/logger.py†L37-L55】 |
| `priority` | `str` | Non | Injecté dans `llm_analysis` afin de pondérer la télémétrie et les alertes.【F:AGI_Evolutive/runtime/logger.py†L37-L55】 |
| `notes` | `str` | Non | Ajouté à l'analyse LLM pour expliquer l'événement archivé.【F:AGI_Evolutive/runtime/logger.py†L37-L55】 |

### `runtime_analytics` — `AGI_Evolutive/runtime/analytics.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `summary` | `str` | Non | Stocké dans `last_output` et écrit dans le journal JSONL pour audit.【F:AGI_Evolutive/runtime/analytics.py†L67-L119】 |
| `alerts` | liste de mappings | Non | Ajoutées à l'analyse persistée pour suivre les risques signalés.【F:AGI_Evolutive/runtime/analytics.py†L84-L119】 |
| `recommendations` | liste de `str` | Non | Restituées dans l'analyse LLM et transmises aux opérateurs.【F:AGI_Evolutive/runtime/analytics.py†L84-L119】 |

### `runtime_job_manager` — `AGI_Evolutive/runtime/job_manager.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `prioritized_jobs` | liste de mappings | Oui | Le premier `job_id` valide déclenche l'exécution, sinon le job est marqué `llm_missing_selection`.【F:AGI_Evolutive/runtime/job_manager.py†L219-L276】 |
| `prioritized_jobs[*].job_id` | `str` | Oui | Identifiant appliqué pour passer le job en état `running`.【F:AGI_Evolutive/runtime/job_manager.py†L233-L248】 |
| `prioritized_jobs[*].rationale` | `str` | Non | Recopié dans `job.llm_notes` et journalisé dans l'historique.【F:AGI_Evolutive/runtime/job_manager.py†L244-L276】 |
| `notes` | `str` | Non | Conservé dans `history` pour éclairer les décisions futures.【F:AGI_Evolutive/runtime/job_manager.py†L269-L276】 |

### `scheduler` — `AGI_Evolutive/runtime/scheduler.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `actions` | liste de mappings | Non | Chaque action validée est appliquée via `_resolve_target`; sinon seule la journalisation est effectuée.【F:AGI_Evolutive/runtime/scheduler.py†L59-L157】 |
| `actions[*].target` | `str` | Non | Objet visé par la méthode d'entretien (`arch`, `jobs`, etc.).【F:AGI_Evolutive/runtime/scheduler.py†L145-L164】 |
| `actions[*].method` | `str` | Non | Méthode invoquée sur la cible pour réaliser l'ajustement.【F:AGI_Evolutive/runtime/scheduler.py†L145-L155】 |
| `actions[*].args` | mapping | Non | Paramètres transmis après normalisation JSON.【F:AGI_Evolutive/runtime/scheduler.py†L145-L155】 |

### `system_monitor` — `AGI_Evolutive/runtime/system_monitor.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `observations` | liste de mappings | Non | Intégrées dans `llm_analysis` pour interpréter les mesures collectées.【F:AGI_Evolutive/runtime/system_monitor.py†L34-L137】 |
| `risks` | liste de `str` | Non | Reprises dans la sortie afin d'alimenter homéostasie et alertes opérateur.【F:AGI_Evolutive/runtime/system_monitor.py†L34-L137】 |
| `notes` | `str` | Non | Ajouté au commentaire pour documenter les recommandations.【F:AGI_Evolutive/runtime/system_monitor.py†L34-L137】 |

### `phenomenal_kernel` — `AGI_Evolutive/runtime/phenomenal_kernel.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `energy` / `arousal` / `hedonic_reward` | nombre ∈ [0, 1] | Non | Mises à jour dans `state` pour guider les modules émotionnels.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L90-L125】 |
| `recommended_mode` | `str` | Non | Propagé dans `state` et exploité par le mode manager.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L90-L125】 |
| `justification` | `str` | Non | Conservé dans `state` pour analyser la décision du modèle.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L90-L125】 |

### `phenomenal_mode_manager` — `AGI_Evolutive/runtime/phenomenal_kernel.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `mode` | `str` (`travail`/`flanerie`) | Oui | Détermine le mode courant et ajuste les budgets de jobs.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L141-L157】 |
| `flanerie_ratio` | nombre ∈ [0, 1] | Non | Journalisé dans l'historique pour calibrer les transitions futures.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L141-L157】 |
| `flanerie_budget_remaining` | nombre | Non | Sert à calculer le ralentissement appliqué aux files.【F:AGI_Evolutive/orchestrator.py†L2284-L2312】 |
| `justification` | `str` | Non | Enrichit le log phénoménologique lors du changement de mode.【F:AGI_Evolutive/runtime/phenomenal_kernel.py†L141-L157】 |

### `runtime_dash` — `AGI_Evolutive/runtime/dash.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `daily_summary` | `str` | Non | Restitué dans le rapport pour synthétiser les métriques observées.【F:AGI_Evolutive/runtime/dash.py†L30-L48】 |
| `recommended_actions` | liste de mappings | Non | Chaque action est conservée dans `report["analysis"]` pour guider les opérateurs.【F:AGI_Evolutive/runtime/dash.py†L30-L48】 |
| `notes` | `str` | Non | Ajouté au rapport final afin de documenter le contexte du jour.【F:AGI_Evolutive/runtime/dash.py†L30-L48】 |

### `response_formatter` — `AGI_Evolutive/runtime/response.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `message` | `str` | Oui | Réponse finale renvoyée à l'appelant (`humanize_reasoning_block`, `format_agent_reply`).【F:AGI_Evolutive/runtime/response.py†L44-L88】 |
| `diagnostics.hypothese` | `str` | Non | Conservé dans les diagnostics pour instrumentation UI.【F:AGI_Evolutive/runtime/response.py†L44-L88】 |
| `diagnostics.incertitude` | nombre ∈ [0, 1] | Non | Met à jour la confiance affichée aux utilisateurs.【F:AGI_Evolutive/runtime/response.py†L44-L88】 |
| `diagnostics.besoins` / `diagnostics.questions` | liste de `str` | Non | Propagées aux rappels conversationnels et à la télémétrie.【F:AGI_Evolutive/runtime/response.py†L44-L88】 |

### `response_contract` — `AGI_Evolutive/runtime/response.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `hypothese` | `str` | Oui | Devient l'hypothèse de travail dans `last_contract`.【F:AGI_Evolutive/runtime/response.py†L28-L42】 |
| `incertitude` | nombre ∈ [0, 1] | Oui | Stocké pour guider les reformulations ultérieures.【F:AGI_Evolutive/runtime/response.py†L28-L42】 |
| `prochain_test` | `str` | Non | Inséré dans les réponses pour cadrer la prochaine étape.【F:AGI_Evolutive/runtime/response.py†L28-L42】 |
| `appris` | liste de `str` | Non | Documente les apprentissages dans l'état interne.【F:AGI_Evolutive/runtime/response.py†L28-L42】 |
| `besoins` | liste de `str` | Non | Alimente les sections « besoins » des messages formatés.【F:AGI_Evolutive/runtime/response.py†L28-L42】 |

## Perception

### `perception_module` — `AGI_Evolutive/perception/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `observations` | liste de mappings | Non | Archivée dans `scene.background["llm_analysis"]` pour audit visuel.【F:AGI_Evolutive/perception/__init__.py†L41-L82】 |
| `recommended_settings` | mapping | Non | Appliqué à `perceptual_parameters` lorsque les valeurs sont numériques.【F:AGI_Evolutive/perception/__init__.py†L58-L82】 |
| `notes` | `str` | Non | Stocké dans le résumé LLM pour contextualiser les ajustements.【F:AGI_Evolutive/perception/__init__.py†L58-L82】 |

## World model

### `world_model` — `AGI_Evolutive/world_model/__init__.py`

| Champ | Type attendu | Obligatoire | Effet runtime |
| --- | --- | --- | --- |
| `action` | `str` | Non | Recommandation appliquée telle quelle aux consommateurs (scheduler, opérateur).【F:AGI_Evolutive/world_model/__init__.py†L13-L55】 |
| `scenarios` | mapping | Non | Décrit les scénarios (optimiste/neutre/pessimiste) conservés pour l'analyse d'impact.【F:AGI_Evolutive/world_model/__init__.py†L13-L55】 |
| `probabilities` | mapping | Non | Sert à calibrer les décisions côté orchestrateur.【F:AGI_Evolutive/world_model/__init__.py†L13-L55】 |
| `notes` | `str` | Non | Ajouté à l'historique interne pour tracer les explications du modèle.【F:AGI_Evolutive/world_model/__init__.py†L13-L55】 |
