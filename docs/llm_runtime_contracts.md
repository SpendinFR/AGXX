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
