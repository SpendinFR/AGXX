# Public entry points inventory

Generated inventory of top-level classes, functions, and other statements per module in `AGI_Evolutive`.

Existing LLM wrapper helpers that only front single heuristics will be removed during the refactor and therefore are not treated as final entry points.

Each section lists definitions and statements that will be considered for consolidation into single-call LLM orchestrators.

## __init__.py

### Classes
- *(none)*

### Functions
- `package_overview`
- _(private)_ `_collect_package_stats`, `_normalise_llm_overview`, `_fallback_overview`, `_clean_string`, `_clean_string_list`, `_safe_confidence`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- from pathlib import Path
- from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_PACKAGE_NAME`
- Assignment to `_PACKAGE_ROOT`
- Assignment to `__all__`

## autonomy/__init__.py

### Classes
- `AgendaItem`
- `AdaptiveEMA`
- `StreamingCorrelation`
- `OnlineWeightLearner`
- `MetricLearningState`
- `AutonomyManager`

### Functions
- *(none)*

### Other top-level statements
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- from collections import deque, from collections import defaultdict
- import logging
- import os, import time, import uuid, import json, import threading, import random, import math
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.goals import GoalType, from AGI_Evolutive.goals import GoalMetadata
- from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry, from AGI_Evolutive.autonomy.auto_signals import AutoSignal
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Module docstring
- from core import AutonomyCore
- Assignment to `__all__`

## autonomy/auto_evolution.py

### Classes
- `AutoIntention`
- `AutoEvolutionCoordinator`

### Functions
- _(private)_ `_slugify`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import re
- import threading
- import time
- from collections import OrderedDict
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.autonomy.auto_signals import derive_signals_for_description, from AGI_Evolutive.autonomy.auto_signals import extract_keywords
- from AGI_Evolutive.core.structures.mai import ImpactHypothesis, from AGI_Evolutive.core.structures.mai import MAI
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level try block
- Assignment to `logger`
- Assignment to `__all__`

## autonomy/auto_signals.py

### Classes
- `AutoSignal`
- `AutoSignalRegistry`

### Functions
- `extract_keywords`
- `derive_signals_for_description`
- _(private)_ `_normalise_keyword`, `_metric_from_keyword`, `_direction_for_keyword`, `_target_for_keyword`, `_weight_for_keyword`, `_derive_signal_templates`, `_heuristic_signal_derivation`, `_llm_signal_derivation`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import re
- import time
- from dataclasses import dataclass, from dataclasses import field
- import unicodedata
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `NEGATIVE_HINTS`
- Assignment to `__all__`

## autonomy/core.py

### Classes
- `AutonomyCore`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import math
- import random
- import threading
- import time
- import logging
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.goals.dag_store import GoalDAG
- from AGI_Evolutive.reasoning.structures import Evidence, from AGI_Evolutive.reasoning.structures import Hypothesis, from AGI_Evolutive.reasoning.structures import Test, from AGI_Evolutive.reasoning.structures import episode_record
- from AGI_Evolutive.runtime.logger import JSONLLogger
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## beliefs/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from graph import BeliefGraph, from graph import Belief, from graph import Evidence, from graph import Event, from graph import TemporalSegment
- from ontology import Ontology
- from entity_linker import EntityLinker
- from summarizer import BeliefSummarizer
- Assignment to `__all__`

## beliefs/adaptation.py

### Classes
- `FeedbackStats`
- `ThompsonParameter`
- `RuleCandidate`
- `FeedbackTracker`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import asdict
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Iterator, from typing import Mapping, from typing import Optional, from typing import Tuple
- import json
- import logging
- import math
- import os
- import random
- import time
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## beliefs/entity_linker.py

### Classes
- `EntityRecord`
- `AdaptiveWeighter`
- `EntityLinker`

### Functions
- _(private)_ `_sigmoid`, `_logit`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import time
- from collections import defaultdict
- from dataclasses import dataclass, from dataclasses import field
- from typing import Dict, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## beliefs/graph.py

### Classes
- `Evidence`
- `TemporalSegment`
- `Belief`
- `Event`
- `LocalRule`
- `BeliefGraph`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field, from dataclasses import asdict
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Iterable, from typing import Tuple, from typing import TYPE_CHECKING, from typing import Mapping
- import os, import json, import time, import uuid, import math, import logging
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from adaptation import FeedbackTracker
- from ontology import Ontology
- from entity_linker import EntityLinker
- Top-level if statement
- Assignment to `LOGGER`

## beliefs/ontology.py

### Classes
- `EntityType`
- `RelationType`
- `EventType`
- `Ontology`

### Functions
- _(private)_ `_coerce_confidence`, `_coerce_bool`, `_ensure_str_list`, `_normalized_name`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- from dataclasses import dataclass
- from pathlib import Path
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional, from typing import Set
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_LLM_SPEC_KEY`
- Assignment to `_LLM_CONFIDENCE_THRESHOLD`
- Assignment to `_LLM_SNAPSHOT_LIMIT`
- Assignment to `_CACHE_MISS`
- Assignment to `logger`

## beliefs/summarizer.py

### Classes
- `SummaryConfig`
- `AdaptiveWeights`
- `SummaryVariant`
- `BeliefSummarizer`

### Functions
- `run_batch`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import random
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from graph import Belief, from graph import BeliefGraph
- Assignment to `LOGGER`
- Assignment to `DEFAULT_CONFIGS`

## cognition/__init__.py

### Classes
- *(none)*

### Functions
- `summarize_cognition_state`
- _(private)_ `_safe_len`, `_collect_planner_snapshot`, `_collect_feedback_snapshot`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from typing import Any, from typing import Dict, from typing import Mapping, from typing import MutableMapping
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `__all__`
- Module docstring
- Module docstring
- from planner import Planner
- from homeostasis import Homeostasis
- from proposer import Proposer

## cognition/context_inference.py

### Classes
- `ContextInferenceError`
- `WhereState`
- `WhereDirective`

### Functions
- `infer_where_and_apply`
- _(private)_ `_normalise_string`, `_normalise_mapping`, `_normalise_sequence`, `_snapshot_self_model`, `_recent_memories`, `_job_manager_snapshot`, `_build_payload`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager

## cognition/evolution_manager.py

### Classes
- `ThompsonBandit`
- `EvolutionManager`

### Functions
- _(private)_ `_now`, `_safe_write_json`, `_safe_read_json`, `_append_jsonl`, `_mean`, `_rolling`, `_clamp01`

### Other top-level statements
- import json
- import logging
- import os
- import random
- import statistics
- import threading
- import time
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Sequence, from typing import Union
- from AGI_Evolutive.core.structures.mai import MAI
- from AGI_Evolutive.knowledge.mechanism_store import MechanismStore
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## cognition/habit_system.py

### Classes
- `HabitRoutine`
- `HabitSystem`

### Functions
- _(private)_ `_clamp`, `_parse_time_of_day`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import os
- import time
- from dataclasses import dataclass, from dataclasses import field
- from datetime import datetime, from datetime import time as dtime
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `__all__`

## cognition/homeostasis.py

### Classes
- `HomeostasisDirective`
- `Homeostasis`

### Functions
- _(private)_ `_now`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import os
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import MutableMapping, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from AGI_Evolutive.core.config import cfg
- Assignment to `logger`
- Assignment to `_DEFAULT_DRIVES`

## cognition/identity_mission.py

### Classes
- `IdentityMissionDirective`

### Functions
- `recommend_and_apply_mission`
- _(private)_ `_ensure_state`, `_collect_context`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `__all__`

## cognition/identity_principles.py

### Classes
- *(none)*

### Functions
- `extract_effective_policies`
- `map_to_principles`
- `propose_commitments`
- `run_and_apply_principles`
- _(private)_ `_bounded_append`, `_success_rate`, `_parse_float`, `_collect_history`, `_collect_commitment_impact`, `_slugify`, `_resolve_policy`, `_collect_policy_stats`, `_strength_from_history`, `_principles_changed`, `_record_principles_application`, `_llm_refine_principles`

### Other top-level statements
- import time
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Set, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_HISTORY_ALIAS`

## cognition/meta_cognition.py

### Classes
- `OnlineLinear`
- `MetaCognition`

### Functions
- _(private)_ `_llm_enabled`, `_llm_manager`

### Other top-level statements
- import hashlib
- import logging
- import math
- import os
- import json
- import random
- import time
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Iterable, from typing import Tuple, from typing import Mapping
- from collections import Counter
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `STOPWORDS`
- Assignment to `TRIVIAL_GOAL_TOKENS`
- Assignment to `POSITIVE_WORDS`
- Assignment to `NEGATIVE_WORDS`
- Assignment to `DOMAIN_KEYWORDS`
- Assignment to `TTL_OPTIONS`
- Assignment to `LOGGER`

## cognition/pipelines_registry.py

### Classes
- `Stage`
- `ActMode`
- `PipelineDescriptor`
- `PolicySelection`
- `PipelinePolicy`

### Functions
- `evaluate_condition`
- `should_skip_stage`
- `describe_registry`
- _(private)_ `_ACT`, `_resolve_ctx_path`, `_compare`, `_mode_reflex_if_immediate`, `_mode_habit_if_low_importance`, `_normalize_skip`, `_normalize_steps`, `_default_descriptors`, `_load_external_descriptors`, `_merge_descriptors`, `_build_registry`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import os
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum, from enum import auto
- from pathlib import Path
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `ConditionSpec`
- Assignment to `CONDITION_PRESETS`
- Assignment to `MODE_SELECTORS`
- Assignment to `CONFIG_ENV`
- Assignment to `CONFIG_DEFAULT_PATH`
- Assignment to `_DESCRIPTORS`
- Assignment to `REGISTRY`
- Assignment to `PIPELINE_POLICY`
- Assignment to `__all__`

## cognition/planner.py

### Classes
- `PlannerError`
- `PlannerStep`
- `PlannerPlan`
- `Planner`

### Functions
- _(private)_ `_coerce_str`, `_coerce_float`, `_coerce_list`, `_coerce_mapping`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import os
- import threading
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.core.config import cfg
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `LOGGER`
- Assignment to `_PLANS`

## cognition/preferences_inference.py

### Classes
- *(none)*

### Functions
- `infer_preferences`
- `apply_preferences_if_confident`
- _(private)_ `_memory_recent`, `_flatten_text_fragments`, `_decay_weight`, `_extract_language_from_text`, `_extract_sentiment_tokens`

### Other top-level statements
- from collections import Counter
- from math import exp
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict

## cognition/principle_inducer.py

### Classes
- `PrincipleInducer`
- _(private)_ `_FeedbackRecord`, `_FeedbackLedger`, `_TelemetryLogger`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- import json
- import math
- import random
- import statistics
- import time
- from collections import defaultdict
- from dataclasses import dataclass
- from pathlib import Path
- import hashlib
- from AGI_Evolutive.core.structures.mai import MAI, from AGI_Evolutive.core.structures.mai import new_mai, from AGI_Evolutive.core.structures.mai import EvidenceRef, from AGI_Evolutive.core.structures.mai import ImpactHypothesis
- from AGI_Evolutive.knowledge.mechanism_store import MechanismStore
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `NormativePattern`

## cognition/prioritizer.py

### Classes
- `PrioritizationError`
- `GoalSnapshot`
- `PrioritizedGoal`
- `PrioritizationDirective`
- `GoalPrioritizer`

### Functions
- _(private)_ `_normalise_string`, `_normalise_tags`, `_normalise_float`, `_normalise_mapping`, `_normalise_sequence`, `_planner_plans`, `_global_context`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager

## cognition/proposer.py

### Classes
- `Proposer`

### Functions
- *(none)*

### Other top-level statements
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping
- import logging
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## cognition/reflection_loop.py

### Classes
- `ReflectionLoop`

### Functions
- _(private)_ `_llm_enabled`, `_llm_manager`

### Other top-level statements
- import logging
- import time, import threading
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Mapping
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`

## cognition/reward_engine.py

### Classes
- `RewardEvent`
- `OnlineCalibratedClassifier`
- `RewardEngine`

### Functions
- *(none)*

### Other top-level statements
- from dataclasses import dataclass, from dataclasses import asdict
- from typing import Optional, from typing import Dict, from typing import Any, from typing import List, from typing import Tuple, from typing import Callable
- import logging
- import math
- import re
- import time
- import json
- import os
- from collections import deque
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.goals import GoalType
- from AGI_Evolutive.goals.curiosity import CuriosityEngine
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## cognition/thinking_monitor.py

### Classes
- `ThinkingSnapshot`
- `ThinkingMonitor`

### Functions
- _(private)_ `_safe_clip`

### Other top-level statements
- from __future__ import annotations
- import logging
- import time
- from collections import deque
- from dataclasses import dataclass
- from typing import Deque, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## cognition/trigger_bus.py

### Classes
- `ScoredTrigger`
- `OnlineLinear`
- `DiscreteThompsonSampler`
- `TriggerBus`

### Functions
- *(none)*

### Other top-level statements
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- from dataclasses import dataclass
- import hashlib
- import json
- import math
- import random
- import time
- from AGI_Evolutive.core.trigger_types import Trigger, from AGI_Evolutive.core.trigger_types import TriggerType
- from AGI_Evolutive.core.evaluation import get_last_priority_token, from AGI_Evolutive.core.evaluation import record_priority_feedback, from AGI_Evolutive.core.evaluation import unified_priority
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `Collector`

## cognition/trigger_router.py

### Classes
- `TriggerRouter`

### Functions
- *(none)*

### Other top-level statements
- import logging
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.core.trigger_types import Trigger, from AGI_Evolutive.core.trigger_types import TriggerType
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## cognition/understanding_aggregator.py

### Classes
- `UnderstandingResult`
- `UnderstandingAggregator`
- _(private)_ `_ThompsonBandit`

### Functions
- _(private)_ `_llm_enabled`, `_llm_manager`, `_clamp`

### Other top-level statements
- from __future__ import annotations
- import random
- import logging
- from dataclasses import dataclass
- from typing import Dict, from typing import Iterable, from typing import Optional, from typing import Mapping
- from AGI_Evolutive.cognition.meta_cognition import OnlineLinear
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`

## conversation/context.py

### Classes
- `ConversationContextError`
- `ConversationMessage`
- `LLMConversationContext`
- `ContextBuilder`

### Functions
- _(private)_ `_normalize_text`, `_coerce_float`, `_coerce_string`, `_coerce_string_list`, `_coerce_mapping`, `_coerce_action_list`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import unicodedata
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## core/__init__.py

### Classes
- _(private)_ `_CoreComponent`

### Functions
- `core_overview`
- _(private)_ `_component_snapshot`, `_fallback_overview`, `_normalise_llm_overview`, `_clean_str`, `_clean_list`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import importlib
- import inspect
- import logging
- from dataclasses import dataclass
- from typing import Iterable, from typing import MutableMapping, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_CORE_COMPONENTS`
- Assignment to `__all__`

## core/autopilot.py

### Classes
- `StageState`
- `StageResult`
- `StageExecutionError`
- `Autopilot`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import inspect
- import logging
- import os
- import time
- import uuid
- from collections import deque
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional
- from config import cfg
- from document_ingest import DocumentIngest
- from persistence import PersistenceManager
- from question_manager import QuestionManager
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict

## core/cognitive_architecture.py

### Classes
- `CognitiveArchitecture`

### Functions
- *(none)*

### Other top-level statements
- import json
- import datetime as dt
- import logging
- import os
- import re
- import time
- import unicodedata
- from collections import deque
- from copy import deepcopy
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Set, from typing import Tuple
- from AGI_Evolutive.autonomy import AutonomyManager
- from AGI_Evolutive.autonomy.auto_evolution import AutoEvolutionCoordinator
- from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry
- from AGI_Evolutive.beliefs.graph import BeliefGraph, from AGI_Evolutive.beliefs.graph import Evidence
- from AGI_Evolutive.knowledge.ontology_facade import EntityLinker, from AGI_Evolutive.knowledge.ontology_facade import Ontology
- from AGI_Evolutive.cognition.evolution_manager import EvolutionManager
- from AGI_Evolutive.cognition.reward_engine import RewardEngine, from AGI_Evolutive.cognition.reward_engine import RewardEvent
- from AGI_Evolutive.core.telemetry import Telemetry
- from AGI_Evolutive.core.question_manager import QuestionManager
- from AGI_Evolutive.creativity import CreativitySystem
- from AGI_Evolutive.emotions import EmotionalSystem
- from AGI_Evolutive.goals import GoalSystem, from AGI_Evolutive.goals import GoalType
- from AGI_Evolutive.goals.dag_store import GoalDAG
- from AGI_Evolutive.io.action_interface import ActionInterface
- from AGI_Evolutive.io.perception_interface import PerceptionInterface
- from AGI_Evolutive.language.understanding import SemanticUnderstanding
- from AGI_Evolutive.language.style_policy import StylePolicy
- from AGI_Evolutive.language.social_reward import extract_social_reward
- from AGI_Evolutive.language.style_profiler import StyleProfiler
- from AGI_Evolutive.language.nlg import NLGContext, from AGI_Evolutive.language.nlg import apply_mai_bids_to_nlg
- from AGI_Evolutive.learning import ExperientialLearning
- from AGI_Evolutive.memory import MemorySystem
- from AGI_Evolutive.memory.concept_extractor import ConceptExtractor
- from AGI_Evolutive.memory.episodic_linker import EpisodicLinker
- from AGI_Evolutive.memory.vector_store import VectorStore
- from AGI_Evolutive.retrieval.adaptive_controller import RAGAdaptiveController
- from AGI_Evolutive.metacog.calibration import CalibrationMeter, from AGI_Evolutive.metacog.calibration import NoveltyDetector
- from AGI_Evolutive.metacognition import MetacognitiveSystem
- from AGI_Evolutive.models import IntentModel, from AGI_Evolutive.models import UserModel
- from AGI_Evolutive.perception import PerceptionSystem
- from AGI_Evolutive.reasoning import ReasoningSystem
- from AGI_Evolutive.reasoning.abduction import AbductiveReasoner, from AGI_Evolutive.reasoning.abduction import Hypothesis
- from AGI_Evolutive.reasoning.causal import CounterfactualSimulator, from AGI_Evolutive.reasoning.causal import SCMStore
- from AGI_Evolutive.reasoning.question_engine import QuestionEngine
- from AGI_Evolutive.runtime.logger import JSONLLogger
- from AGI_Evolutive.runtime.response import ensure_contract, from AGI_Evolutive.runtime.response import format_agent_reply, from AGI_Evolutive.runtime.response import humanize_reasoning_block
- from AGI_Evolutive.runtime.scheduler import Scheduler
- from AGI_Evolutive.runtime.job_manager import JobManager
- from AGI_Evolutive.world_model import PhysicsEngine
- from AGI_Evolutive.self_improver import SelfImprover
- from AGI_Evolutive.self_improver.code_evolver import CodeEvolver
- from AGI_Evolutive.self_improver.promote import PromotionManager
- from AGI_Evolutive.self_improver.skill_acquisition import SkillSandboxManager
- from AGI_Evolutive.planning.htn import HTNPlanner
- from AGI_Evolutive.core.persistence import PersistenceManager
- from AGI_Evolutive.core.self_model import SelfModel
- from AGI_Evolutive.core.config import cfg
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## core/config.py

### Classes
- *(none)*

### Functions
- `load_config`
- `cfg`
- `summarize_config`
- _(private)_ `_fallback_summary`, `_clean_text`, `_clean_list`

### Other top-level statements
- import json
- import logging
- import os
- from functools import lru_cache
- from typing import Any, from typing import Dict, from typing import Mapping, from typing import MutableMapping, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_DEFAULTS`
- Assignment to `_DIR_KEYS`
- Assignment to `_cfg`
- Assignment to `LOGGER`

## core/consciousness_engine.py

### Classes
- `ConsciousnessEngine`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from global_workspace import GlobalWorkspace
- Assignment to `LOGGER`
- Assignment to `__all__`

## core/decision_journal.py

### Classes
- `DecisionJournal`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- import time
- import uuid
- from typing import Any, from typing import Dict, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/document_ingest.py

### Classes
- `DocumentIngest`

### Functions
- _(private)_ `_hash`, `_summarize_text`, `_document_evidence_job`

### Other top-level statements
- Module docstring
- import logging
- import os
- import time
- import glob
- from typing import Dict, from typing import Any, from typing import Iterable
- from AGI_Evolutive.core.config import cfg
- from AGI_Evolutive.knowledge.concept_recognizer import ConceptRecognizer
- from AGI_Evolutive.memory import MemoryType
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/evaluation.py

### Classes
- `PriorityContext`
- `OnlinePriorityModel`
- `PriorityBandit`
- `PriorityLogger`
- `PriorityManager`

### Functions
- `unified_priority`
- `get_last_priority_token`
- `record_priority_feedback`
- _(private)_ `_clamp`, `_heuristic_priority`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import atexit
- import json
- import math
- import os
- import random
- import threading
- import time
- from dataclasses import asdict, from dataclasses import dataclass
- from pathlib import Path
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional, from typing import Tuple
- import logging
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`
- Assignment to `_MANAGER`

## core/executive_control.py

### Classes
- `ExecutiveControl`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- from typing import Any, from typing import Dict, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`

## core/global_workspace.py

### Classes
- `ThompsonBandit`
- `GlobalWorkspace`

### Functions
- _(private)_ `_heuristic_info_gain`, `_rag_features`, `_score_features`, `_urgency_from_frame`, `_truncate_payload`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import os
- import random
- import time
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.cognition.meta_cognition import OnlineLinear
- from AGI_Evolutive.core.structures.mai import Bid
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/life_story.py

### Classes
- `GeneticProfile`
- `LifeStoryManager`

### Functions
- `ensure_genetics_structure`
- `ensure_story_structure`
- _(private)_ `_clamp`, `_normalize_label`, `_ensure_list_of_dicts`, `_normalize_tags`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import copy
- import math
- import logging
- import time
- import unicodedata
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_DEFAULT_TRAITS`
- Assignment to `_DEFAULT_DRIVES`
- Assignment to `_DEFAULT_SCRIPTS`
- Assignment to `_DEFAULT_AWAKENING_CHECKPOINTS`
- Assignment to `__all__`

## core/persistence.py

### Classes
- `StorageBackend`
- `FileStorageBackend`
- `PersistenceManager`

### Functions
- `register_migration`
- _(private)_ `_is_picklable`, `_to_state`, `_from_state`

### Other top-level statements
- Module docstring
- import hashlib
- import inspect
- import json
- import logging
- import os
- import pickle
- import time
- import types
- from datetime import datetime
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `DEFAULT_DIR`
- Assignment to `DEFAULT_DIR`
- Assignment to `DEFAULT_FILE`
- Assignment to `MigrationCallable`
- Assignment to `_MIGRATIONS`

## core/policy.py

### Classes
- `PolicyEngine`
- _(private)_ `_ThompsonBidSelector`

### Functions
- `rag_quality_signal`

### Other top-level statements
- from __future__ import annotations
- from collections import defaultdict
- from dataclasses import asdict
- from math import sqrt
- from typing import Callable, from typing import Dict, from typing import Any, from typing import List, from typing import Optional, from typing import Tuple
- import logging
- import random, import copy, import json, import os, import time
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.knowledge.mechanism_store import MechanismStore
- from AGI_Evolutive.core.structures.mai import MAI, from AGI_Evolutive.core.structures.mai import Bid
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/question_manager.py

### Classes
- `LinearBanditScorer`
- `QuestionManager`
- _(private)_ `_FeatureHasher`

### Functions
- _(private)_ `_clip`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import math
- import time
- import uuid
- from collections import deque
- import re
- from typing import Any, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- import logging
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Top-level try block

## core/reasoning_ledger.py

### Classes
- `Premise`
- `Option`
- `CounterExample`
- `Trace`
- `ReasoningLedger`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- import time
- import uuid
- from dataclasses import dataclass, from dataclasses import field
- from typing import Dict, from typing import List, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/self_model.py

### Classes
- `SelfModel`

### Functions
- *(none)*

### Other top-level statements
- import copy
- import json
- import logging
- import math
- import os
- import time
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple, from typing import Mapping
- from AGI_Evolutive.core.config import cfg
- from AGI_Evolutive.core.life_story import GeneticProfile, from AGI_Evolutive.core.life_story import LifeStoryManager, from AGI_Evolutive.core.life_story import ensure_genetics_structure, from AGI_Evolutive.core.life_story import ensure_story_structure
- from AGI_Evolutive.utils import now_iso, from AGI_Evolutive.utils import safe_write_json
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_DEFAULT_SELF`

## core/selfhood_engine.py

### Classes
- `OnlineRegressor`
- `EMABandit`
- `IdentityTraits`
- `Claim`
- `SelfhoodEngine`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- import math
- import random
- import time
- from dataclasses import asdict, from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict

## core/structures/mai.py

### Classes
- `EvidenceRef`
- `ImpactHypothesis`
- `Bid`
- `MAI`

### Functions
- `eval_expr`
- `new_mai`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import time
- import uuid
- import random
- from dataclasses import dataclass, from dataclasses import field, from dataclasses import asdict, from dataclasses import replace
- from typing import Any, from typing import Callable, from typing import ClassVar, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.cognition.meta_cognition import OnlineLinear
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `Expr`
- Assignment to `__all__`

## core/telemetry.py

### Classes
- `Telemetry`

### Functions
- *(none)*

### Other top-level statements
- import json
- import logging
- import os
- import time
- from collections import deque
- from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/timeline_manager.py

### Classes
- `TimelineManager`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import logging
- import time
- from collections import defaultdict
- from copy import deepcopy
- from difflib import SequenceMatcher
- from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## core/trigger_types.py

### Classes
- `TriggerType`
- `Trigger`

### Functions
- `classify_trigger`
- _(private)_ `_heuristic_trigger`, `_parse_trigger_type`, `_clean_text`

### Other top-level statements
- import logging
- from enum import Enum, from enum import auto
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`

## creativity/__init__.py

### Classes
- `IdeaState`
- `InsightType`
- `CreativeIdea`
- `ConceptualBlend`
- `CreativeInsight`
- `InnovationProject`
- `OnlineLogisticModel`
- `AdaptiveCreativeMetrics`
- `ContextualThompsonBandit`
- `DiscreteThompsonSelector`
- `ActivationSpreadingSystem`
- `CreativitySystem`

### Functions
- `crea_normalize`
- _(private)_ `_clip`, `_is_ci`, `_ensure_ci`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import time
- import random
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple, from typing import Mapping
- from collections import defaultdict, from collections import deque
- Top-level try block
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`

## emotions/__init__.py

### Classes
- `BoundedOnlineLinear`
- `DiscreteThompsonSampler`
- `AdaptiveEMARegressor`
- `EmotionDriftDetector`
- `EmotionalHyperAdaptationManager`
- `EmotionalState`
- `MoodState`
- `EmotionalIntensity`
- `EmotionalExperience`
- `Mood`
- `EmotionalMemory`
- `EmotionalSystem`
- `RelevanceDetector`
- `GoalCongruenceAssessor`
- `CopingPotentialEvaluator`
- `NormCompatibilityChecker`
- `SelfImplicationAssessor`
- `FacialExpressionGenerator`
- `VocalToneGenerator`
- `BodyLanguageGenerator`
- `VerbalExpressionGenerator`
- `EmotionalConditioningSystem`
- `MoodCongruentMemory`

### Functions
- _(private)_ `_truncate_text`, `_simplify_for_llm`, `_prepare_llm_context`

### Other top-level statements
- Module docstring
- import json
- import logging
- import math
- import random
- import threading
- import time
- from collections import defaultdict, from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from datetime import datetime, from datetime import timedelta
- from enum import Enum
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Set, from typing import Tuple
- import numpy as np
- from emotion_engine import EmotionEngine
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Top-level if statement

## emotions/emotion_engine.py

### Classes
- `AffectState`
- `MoodState`
- `EmotionEpisode`
- `AppraisalOutput`
- `AppraisalPlugin`
- `CognitiveLoadPlugin`
- `ErrorPlugin`
- `SuccessPlugin`
- `RewardPlugin`
- `IntrinsicPleasurePlugin`
- `FatiguePlugin`
- `SocialFeedbackPlugin`
- `PluginMetaController`
- `AppraisalAggregator`
- `ContextAutoSynthesizer`
- `SynthesizedPlugin`
- `HalfLifePlasticity`
- `RitualPlanner`
- `EmotionEngine`

### Functions
- `clip`
- `json_sanitize`
- `label_from_pad`
- _(private)_ `_softmax`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import os
- import json
- import time
- import math
- import uuid
- from collections import defaultdict, from collections import deque
- from dataclasses import dataclass, from dataclasses import field, from dataclasses import asdict
- from typing import Dict, from typing import Any, from typing import Optional, from typing import List, from typing import Tuple, from typing import TYPE_CHECKING
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Top-level if statement
- Assignment to `LOGGER`
- Assignment to `_POSITIVE_EMOTIONS`
- Assignment to `_NEGATIVE_EMOTIONS`
- Assignment to `NEUTRAL`
- Assignment to `EMO_LABELS`
- Top-level if statement

## experimental/patch_creativity.py

### Classes
- *(none)*

### Functions
- `main`

### Other top-level statements
- from pathlib import Path
- import re, import shutil
- Assignment to `TARGET`
- Top-level if statement

## experimental/patch_creativity_hardfix.py

### Classes
- *(none)*

### Functions
- `add_call`

### Other top-level statements
- import re, import sys, import io, import os
- Assignment to `PATH`
- Top-level if statement
- Top-level with statement
- Assignment to `original`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `src`
- Assignment to `guard_func`
- Top-level if statement
- Top-level for loop
- Top-level if statement

## experimental/patch_metacognition.py

### Classes
- *(none)*

### Functions
- `main`

### Other top-level statements
- import re
- from pathlib import Path
- import shutil
- Assignment to `ROOT`
- Assignment to `TARGET`
- Top-level if statement

## experimental/repair_creativity_v2.py

### Classes
- *(none)*

### Functions
- `fix_conditional_assignments`
- `close_missing_parens_before_comment`
- `process_text`
- `main`

### Other top-level statements
- import ast, import re, import sys
- from pathlib import Path
- Assignment to `TARGET`
- Top-level if statement

## experimental/repair_creativity_v3.py

### Classes
- *(none)*

### Functions
- `fix_conditional_assignments`
- `fix_conditional_appends`
- `close_missing_parens_before_comment`
- `process_text`
- `main`

### Other top-level statements
- import ast, import re, import sys
- from pathlib import Path
- Assignment to `TARGET`
- Top-level if statement

## experimental/repair_creativity_v4.py

### Classes
- *(none)*

### Functions
- `close_missing_parens_before_comment`
- `fix_self_paren`
- `try_fix_conditional_assignment`
- `fix_multiline_append`
- `process_text`
- `main`

### Other top-level statements
- import ast, import re, import sys
- from pathlib import Path
- Assignment to `TARGET`
- Assignment to `_cond_assign`
- Assignment to `_append_start`
- Top-level if statement

## experimental/repair_creativity_v5.py

### Classes
- *(none)*

### Functions
- `close_missing_parens_before_comment`
- `fix_self_paren`
- `process_text`
- `main`

### Other top-level statements
- import ast, import re, import sys
- from pathlib import Path
- Assignment to `TARGET`
- Assignment to `APP_START`
- Assignment to `ASSIGN_LINE`
- Top-level if statement

## goals/__init__.py

### Classes
- `GoalType`
- `GoalStatus`
- `GoalMetadata`
- `GoalSystem`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import re
- import time
- import unicodedata
- from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum
- from typing import Any, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Set, from typing import Tuple
- from curiosity import CuriosityEngine
- from dag_store import DagStore, from dag_store import GoalNode
- from heuristics import HeuristicRegistry, from heuristics import default_heuristics
- from intention_classifier import IntentionModel
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `_LLM_METADATA_CONFIDENCE_THRESHOLD`

## goals/curiosity.py

### Classes
- `OnlineLinear`
- `DiscreteThompsonSampler`
- `CuriosityEngine`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import random
- import re
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## goals/dag_store.py

### Classes
- `GoalNode`
- `OnlinePriorityModel`
- `DagStore`
- `GoalDAG`

### Functions
- _(private)_ `_now`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import time
- import uuid
- from dataclasses import asdict, from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Set
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## goals/heuristics.py

### Classes
- `RegexHeuristic`
- `HeuristicRegistry`

### Functions
- `default_heuristics`
- _(private)_ `_llm_enabled`, `_llm_manager`, `_topic_from_match`, `_goal_payload`, `_goal_priority`, `_llm_suggest_actions`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import re
- from collections import deque
- from dataclasses import dataclass
- from typing import Any, from typing import Callable, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional, from typing import Pattern, from typing import List
- from dag_store import GoalNode
- from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `ActionDeque`
- Assignment to `HeuristicFn`
- Assignment to `LOGGER`

## goals/intention_classifier.py

### Classes
- `Prediction`
- `OnlineTextClassifier`
- `IntentionModel`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import re
- from collections import Counter, from collections import defaultdict
- from dataclasses import dataclass
- from typing import TYPE_CHECKING, from typing import Dict, from typing import Optional
- from dag_store import GoalNode
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level if statement
- Assignment to `TOKEN_PATTERN`
- Assignment to `LOGGER`

## io/__init__.py

### Classes
- *(none)*

### Functions
- `describe_io_interfaces`
- _(private)_ `_build_baseline_snapshot`, `_build_interface_entry`, `_safe_import`, `_first_doc_line`, `_merge_snapshots`, `_summarise_context`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import importlib
- import inspect
- import logging
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `_INTERFACE_TEMPLATES`
- Assignment to `__all__`

## io/action_interface.py

### Classes
- `Action`
- `DiscreteThompsonSampling`
- `AdaptiveEMA`
- `ActionStats`
- `PriorityLearner`
- `ActionInterface`

### Functions
- _(private)_ `_now`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import random
- import time
- import uuid
- from collections import deque
- from dataclasses import asdict, from dataclasses import dataclass, from dataclasses import field
- from enum import Enum
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry, from AGI_Evolutive.autonomy.auto_signals import derive_signals_for_description
- from AGI_Evolutive.beliefs.graph import Evidence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level try block
- Assignment to `logger`

## io/intent_classifier.py

### Classes
- `IntentIngestionResult`
- `IntentIngestionOrchestrator`

### Functions
- `analyze`
- _(private)_ `_parse_llm_response`, `_clean_label`, `_optional_str`, `_coerce_float`, `_collect_strings`, `_collect_entities`, `_normalise_entity`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from types import MappingProxyType
- from typing import Any, from typing import Iterable, from typing import Mapping, from typing import MutableMapping
- from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `_default_orchestrator`
- Assignment to `__all__`

## io/perception_interface.py

### Classes
- `PerceptionInterface`

### Functions
- _(private)_ `_now`, `_llm_enabled`, `_llm_manager`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import glob
- import json
- import logging
- import os
- import time
- import uuid
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Mapping
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- Assignment to `LOGGER`

## knowledge/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from ontology_facade import EntityLinker, from ontology_facade import Ontology
- Assignment to `__all__`

## knowledge/concept_recognizer.py

### Classes
- `OnlineConceptModel`
- `ItemCandidate`
- `ConceptRecognizer`

### Functions
- `clamp`
- _(private)_ `_now`, `_norm`, `_clean_term`, `_is_stopish`, `_is_concepty`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Tuple, from typing import Iterable
- import logging
- import re, import time, import json, import os, import unicodedata, import math
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`
- Assignment to `STOP`
- Assignment to `SUF_N`
- Assignment to `SUF_A`
- Assignment to `SUF_V`
- Assignment to `RE_DEF_1`
- Assignment to `RE_DEF_2`
- Assignment to `RE_LABEL`
- Assignment to `RE_QUOTE`
- Assignment to `RE_REFORM`
- Assignment to `RE_RHET_Q`
- Assignment to `RE_IRONY`
- Assignment to `RE_FORMAL`
- Assignment to `RE_SLANG`
- Assignment to `RE_EMOJIS`

## knowledge/mechanism_store.py

### Classes
- `MechanismStore`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- Module docstring
- import getpass
- import json
- import logging
- import os
- import platform
- import threading
- import time
- from collections import defaultdict
- from dataclasses import asdict, from dataclasses import fields, from dataclasses import is_dataclass
- from pathlib import Path
- from typing import Callable, from typing import Dict, from typing import Iterable, from typing import Iterator, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.core.structures.mai import EvidenceRef, from AGI_Evolutive.core.structures.mai import ImpactHypothesis, from AGI_Evolutive.core.structures.mai import MAI
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `SCHEMA_VERSION`
- Assignment to `_ENV_PATH`
- Top-level if statement
- Assignment to `_LEGACY_PATH`
- Assignment to `LOGGER`
- Assignment to `_LLM_SPEC_KEY`
- Assignment to `__all__`

## knowledge/ontology_facade.py

### Classes
- `Ontology`
- `EntityLinker`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import time
- from collections import Counter, from collections import defaultdict
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.beliefs.entity_linker import EntityLinker as _BeliefEntityLinker
- from AGI_Evolutive.beliefs.graph import BeliefGraph
- from AGI_Evolutive.beliefs.ontology import Ontology as _BeliefOntology
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_LLM_SPEC_KEY`

## language/__init__.py

### Classes
- `AdaptiveEMA`
- `OnlineNgramClassifier`
- `Entity`
- `Frame`
- `Utterance`
- `SemanticUnderstanding`
- `PragmaticReasoning`
- `DiscourseState`
- `DiscourseProcessing`
- `LanguageGeneration`

### Functions
- _(private)_ `_json_load`, `_json_save`, `_now`, `_clip`, `_mean`, `_strip_accents`, `_normalize_text`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import importlib
- import json
- import logging
- import math
- import os
- import random
- import re
- import sys
- import time
- import unicodedata
- from collections import Counter, from collections import defaultdict, from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.models.intent import IntentModel
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`
- Assignment to `DATA_DIR`
- Top-level Expr
- Assignment to `LANGUAGE_DATA_DIR`
- Top-level Expr
- Assignment to `CLASSIFIER_STATE_PATH`
- Assignment to `TRACKER_STATE_PATH`
- Assignment to `ALIASES`
- Top-level for loop
- Assignment to `__all__`

## language/dialogue_state.py

### Classes
- `DialogueState`

### Functions
- *(none)*

### Other top-level statements
- from dataclasses import dataclass, from dataclasses import field
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Mapping
- import logging
- import time
- from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## language/frames.py

### Classes
- `DialogueAct`
- `UtteranceFrame`

### Functions
- `analyze_utterance`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum, from enum import auto
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## language/inbox_ingest.py

### Classes
- *(none)*

### Functions
- `ingest_inbox_paths`
- _(private)_ `_hash_path`, `_llm_filter_entries`

### Other top-level statements
- import hashlib
- import logging
- import os
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional
- from  import DATA_DIR, from  import _json_load, from  import _json_save
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `CACHE`
- Assignment to `LLM_SPEC_KEY`
- Assignment to `LOGGER`

## language/lexicon.py

### Classes
- `LiveLexicon`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import random
- import re
- import time
- import unicodedata
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict

## language/nlg.py

### Classes
- `LanguageGenerationError`
- `NLGRequest`
- `NLGResult`
- `LanguageGeneration`
- `NLGContext`

### Functions
- `generate_reply`
- `apply_mai_bids_to_nlg`
- `paraphrase_light`
- `join_tokens`
- _(private)_ `_coerce_string`, `_coerce_string_list`, `_coerce_mapping`, `_coerce_sections`, `_coerce_actions`, `_assemble_sections`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `_default_generator`

## language/quote_memory.py

### Classes
- `Quote`
- `OnlineLinearBandit`
- `OnlineTextModel`
- `QuoteMemory`

### Functions
- *(none)*

### Other top-level statements
- from dataclasses import dataclass, from dataclasses import asdict, from dataclasses import field
- from typing import List, from typing import Optional, from typing import Dict, from typing import Any, from typing import Tuple
- import logging
- import time, import re, import math, import os, import unicodedata, import hashlib
- import numpy as np
- from  import DATA_DIR, from  import _json_load, from  import _json_save
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`

## language/ranker.py

### Classes
- `RankerModel`

### Functions
- `sigmoid`

### Other top-level statements
- import hashlib
- import logging
- import math
- import os
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional
- from  import DATA_DIR, from  import _json_load, from  import _json_save
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## language/renderer.py

### Classes
- `OnlineLogisticModel`
- `OrnamentDecision`
- `OnlineTextClassifier`
- `LanguageRenderer`

### Functions
- _(private)_ `_tokens`, `_build_language_state_snapshot`, `_apply_action_hint`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import asdict, from dataclasses import dataclass
- from typing import Dict, from typing import Any, from typing import List, from typing import Tuple, from typing import Optional, from typing import Iterable
- import logging
- import random
- import re
- import time
- import math
- from AGI_Evolutive.social.tactic_selector import TacticSelector
- from AGI_Evolutive.social.interaction_rule import ContextBuilder
- from AGI_Evolutive.core.structures.mai import MAI
- from nlg import NLGContext, from nlg import apply_mai_bids_to_nlg, from nlg import paraphrase_light, from nlg import join_tokens
- from style_critic import StyleCritic
- from AGI_Evolutive.runtime.response import humanize_reasoning_block
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `TOKEN_PATTERN`
- Assignment to `DIRECT_QUESTION_PATTERN`
- Assignment to `LOGGER`

## language/social_reward.py

### Classes
- *(none)*

### Functions
- `extract_social_reward`
- _(private)_ `_coerce_float`, `_heuristic_reward`, `_merge_llm_response`

### Other top-level statements
- from __future__ import annotations
- import logging
- from typing import Any, from typing import Dict, from typing import List
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `POSITIVE_MARKERS`
- Assignment to `NEGATIVE_MARKERS`
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`

## language/style_critic.py

### Classes
- `SignalSnapshot`
- `AdaptiveSignal`
- `EvolvingSignalModel`
- `StyleCritic`

### Functions
- _(private)_ `_coerce_float`, `_strip_accents`, `_expressive_density`

### Other top-level statements
- from __future__ import annotations
- import logging
- import re
- import unicodedata
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `EMOJI_RE`
- Assignment to `HEDGING_RE`
- Assignment to `DOUBLE_ADVERB_RE`
- Assignment to `COPULA_RE`
- Assignment to `PUNCT_BEFORE_RE`
- Assignment to `PUNCT_AFTER_RE`
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`

## language/style_observer.py

### Classes
- `OnlineLinearModel`
- `StyleObserver`

### Functions
- _(private)_ `_strip_accents`

### Other top-level statements
- from __future__ import annotations
- from typing import Dict, from typing import Any, from typing import List
- import logging
- import math
- import re
- import time
- import unicodedata
- from collections import deque
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`

## language/style_policy.py

### Classes
- `OnlineLinear`
- `ThompsonBandit`
- `StylePolicy`

### Functions
- _(private)_ `_scaled_reward`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import random
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import ClassVar, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `DEFAULT_MODES`
- Assignment to `DEFAULT_TTLS`

## language/style_profiler.py

### Classes
- `UserStyleProfile`
- `OnlineTextClassifier`
- `StyleProfiler`

### Functions
- *(none)*

### Other top-level statements
- from dataclasses import asdict, from dataclasses import dataclass
- from typing import Dict, from typing import Any, from typing import Iterable, from typing import List
- from collections import Counter, from collections import defaultdict
- import logging
- import math
- import os
- import json
- import re
- import unicodedata
- from datetime import datetime
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `LLM_SPEC_KEY`

## language/understanding.py

### Classes
- `SemanticUnderstandingError`
- `LLMUnderstandingResult`
- `SemanticUnderstanding`

### Functions
- _(private)_ `_normalize`, `_coerce_confidence`, `_coerce_optional_string`, `_coerce_string_list`, `_coerce_dialogue_acts`, `_coerce_mapping`, `_coerce_slots`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import unicodedata
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- from dialogue_state import DialogueState
- from frames import DialogueAct, from frames import UtteranceFrame
- Assignment to `__all__`

## language/voice.py

### Classes
- `OnlineTextClassifier`
- `VoiceProfile`

### Functions
- _(private)_ `_default_style`

### Other top-level statements
- from __future__ import annotations
- import json, import os, import time, import math, import re
- import logging
- from typing import Dict, from typing import Any, from typing import List, from typing import Tuple, from typing import Iterable
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `STYLE_KNOBS`

## learning/__init__.py

### Classes
- `LearningEpisode`
- `ContextFeatureEncoder`
- `OnlineLinearModel`
- `ThompsonBandit`
- `ExperientialLearning`
- `MetaLearning`
- `KnowledgeDomain`
- `TransferLearning`
- `ReinforcementLearning`
- `CuriosityEngine`

### Functions
- _(private)_ `_now`, `_safe_mean`, `_hash_str`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import time, import math, import random, import hashlib
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`

## light_scheduler.py

### Classes
- `LightScheduler`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import random
- import time
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `__all__`

## main.py

### Classes
- `CLIAdaptiveFeedback`

### Functions
- `list_inbox`
- `run_cli`
- `main`
- _(private)_ `_get_qm`, `_print_pending`, `_normalize_feedback_text`, `_detect_feedback_label`

### Other top-level statements
- import argparse
- import glob
- import json
- import logging
- import os
- import re
- import sys
- import time
- import traceback
- import unicodedata
- from datetime import datetime
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict, from AGI_Evolutive.utils.llm_service import get_recent_llm_activity
- Assignment to `logger`
- Top-level try block
- Top-level try block
- Top-level try block
- Top-level try block
- from AGI_Evolutive.core.autopilot import Autopilot, from AGI_Evolutive.core.autopilot import StageExecutionError
- from AGI_Evolutive.core.cognitive_architecture import CognitiveArchitecture
- from AGI_Evolutive.cognition.prioritizer import GoalPrioritizer
- from AGI_Evolutive.orchestrator import Orchestrator
- from AGI_Evolutive.language.voice import VoiceProfile
- from AGI_Evolutive.language.lexicon import LiveLexicon
- from AGI_Evolutive.language.style_observer import StyleObserver
- from AGI_Evolutive.conversation.context import ContextBuilder
- from AGI_Evolutive.language.renderer import LanguageRenderer
- from AGI_Evolutive.language import OnlineNgramClassifier
- from AGI_Evolutive.memory.concept_extractor import ConceptExtractor
- from AGI_Evolutive.memory.prefs_bridge import PrefsBridge as PreferencesAdapter
- from AGI_Evolutive.utils.logging_setup import configure_logging
- from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import set_llm_manager
- Assignment to `BANNER`
- Assignment to `HELP_TEXT`
- Assignment to `_FEEDBACK_STATE_PATH`
- Assignment to `_POSITIVE_PATTERNS`
- Assignment to `_NEGATIVE_PATTERNS`
- Assignment to `_POSITIVE_EMOJI_RE`
- Assignment to `_NEGATIVE_EMOJI_RE`
- Top-level if statement

## memory/__init__.py

### Classes
- `MemoryType`
- `MemoryConsolidationState`
- `MemoryTrace`
- `MemoryRetrievalResult`
- `MemorySystem`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- import logging
- import math
- import random
- from typing import Any, from typing import Iterable, from typing import TYPE_CHECKING
- Top-level try block
- import time
- from collections import deque
- from datetime import datetime, from datetime import timedelta
- from typing import Callable, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple, from typing import Union, from typing import Mapping
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum
- import heapq
- import json
- import hashlib
- Top-level try block
- Top-level try block
- Top-level try block
- from adaptive import AdaptiveMemoryParameters, from adaptive import ThompsonBetaScheduler
- from retrieval import MemoryRetrieval
- from summarizer import ProgressiveSummarizer, from summarizer import SummarizerConfig
- from semantic_memory_manager import SemanticMemoryManager as _SummarizationCoordinator
- from semantic_manager import SemanticMemoryManager as _ConceptMemoryManager
- from alltime import LongTermMemoryHub
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level if statement
- Assignment to `LOGGER`
- Assignment to `__all__`
- Assignment to `SemanticMemoryManager`
- Top-level try block
- Top-level if statement

## memory/adaptive.py

### Classes
- `OnlineLinearParameter`
- `ThompsonBetaScheduler`
- `AdaptiveMemoryParameters`

### Functions
- _(private)_ `_sigmoid`, `_logit`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import random
- from collections.abc import MutableMapping
- from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional
- Top-level try block
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/alltime.py

### Classes
- `DigestDetails`
- `LongTermMemoryHub`

### Functions
- _(private)_ `_safe_float`, `_to_utc`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass
- from datetime import datetime, from datetime import timezone
- import logging
- import math
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence, from typing import Set
- import time
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `DAY_SECONDS`

## memory/concept_extractor.py

### Classes
- `ConceptExtractionError`
- `MemoryDocument`
- `ExtractedConcept`
- `ExtractedRelation`
- `ConceptExtractionResult`
- `ConceptExtractor`

### Functions
- _(private)_ `_normalise_text`, `_normalise_string`, `_normalise_float`, `_normalise_tag_list`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import unicodedata
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- from concept_store import ConceptStore
- Assignment to `__all__`

## memory/concept_store.py

### Classes
- `Concept`
- `Relation`
- `ConceptStore`

### Functions
- _(private)_ `_normalise_label`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import time
- import uuid
- from dataclasses import dataclass, from dataclasses import field
- from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Sequence, from typing import TYPE_CHECKING
- Top-level if statement
- Assignment to `__all__`

## memory/consolidator.py

### Classes
- `OnlineLogisticRegression`
- `ExponentialTrend`
- `StreamingTopics`
- `Consolidator`

### Functions
- _(private)_ `_sigmoid`

### Other top-level statements
- import json
- import json
- import logging
- import math
- import os
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/embedding_adapters.py

### Classes
- `AdaptiveSemanticEmbedder`

### Functions
- _(private)_ `_normalize_term`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- from collections import Counter, from collections import OrderedDict
- from threading import Lock
- from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import MutableMapping, from typing import Optional
- from AGI_Evolutive.memory.encoders import tokenize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `__all__`

## memory/encoders.py

### Classes
- `AdaptiveTokenizer`
- `OnlineContextEmbeddings`
- `EncoderMonitor`
- `TinyEncoder`

### Functions
- `tokenize`
- `l2_normalize`
- `cosine`
- _(private)_ `_hash_to_dim`

### Other top-level statements
- import hashlib
- import logging
- import math
- import random
- import re
- from collections import Counter
- from collections.abc import Iterable as IterableABC
- from dataclasses import dataclass
- from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `_BASE_TOKEN_PATTERN`

## memory/episodic_linker.py

### Classes
- `EpisodicLinker`
- _(private)_ `_AdaptiveScheduler`, `_SalienceLearner`

### Functions
- _(private)_ `_now`

### Other top-level statements
- import logging
- import os
- import json
- import time
- import glob
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple, from typing import Mapping
- Top-level try block
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `CAUSE_HINTS`
- Assignment to `REL_NEXT`
- Assignment to `REL_CAUSES`
- Assignment to `REL_REFERS`
- Assignment to `REL_SUPPORTS`
- Assignment to `REL_CONTRADICTS`
- Assignment to `LLM_RELATION_MAP`

## memory/indexing.py

### Classes
- `MatchFeatures`
- `OnlineLinear`
- `DiscreteThompsonSampler`
- `InMemoryIndex`

### Functions
- *(none)*

### Other top-level statements
- import json
- import math
- import random
- import logging
- import time
- from dataclasses import dataclass
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Tuple, from typing import Iterable
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from encoders import TinyEncoder, from encoders import cosine
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/janitor.py

### Classes
- *(none)*

### Functions
- `run_once`
- _(private)_ `_prepare_candidate`, `_apply_batch`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import time
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/memory_store.py

### Classes
- `MemoryStore`
- _(private)_ `_VectorIndex`

### Functions
- _(private)_ `_safe_float`

### Other top-level statements
- import json
- import logging
- import math
- import os
- import re
- import time
- import uuid
- from collections import Counter
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level try block
- Assignment to `logger`

## memory/prefs_bridge.py

### Classes
- `PrefsBridge`

### Functions
- _(private)_ `_norm_concept`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import os
- import time
- from typing import Any, from typing import Dict, from typing import Iterable
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/retrieval.py

### Classes
- `MemoryRetrieval`
- _(private)_ `_BoundedOnlineLinear`, `_OnlineFallbackClassifier`, `_AdaptiveCandidateReranker`

### Functions
- _(private)_ `_normalize_text`

### Other top-level statements
- import logging
- import math
- import re
- import time
- import unicodedata
- from collections import defaultdict
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- Top-level try block
- Top-level try block
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from encoders import TinyEncoder
- from indexing import DiscreteThompsonSampler, from indexing import InMemoryIndex
- from vector_store import VectorStore
- Assignment to `LOGGER`
- Assignment to `_EMOJI_RE`
- Assignment to `_FRENCH_PATTERN`

## memory/salience_scorer.py

### Classes
- `SalienceScorer`
- _(private)_ `_LearningConfig`, `_OnlineLogit`

### Functions
- _(private)_ `_norm01`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import dataclasses
- import logging
- import math
- import random
- import time
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional, from typing import Tuple
- Top-level try block
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/semantic_bridge.py

### Classes
- `SemanticMemoryBridge`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import queue
- import threading
- from contextlib import nullcontext
- from typing import Any, from typing import Dict, from typing import Mapping, from typing import Optional, from typing import Sequence
- Assignment to `LOGGER`
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `__all__`

## memory/semantic_manager.py

### Classes
- `SemanticMemoryManager`
- _(private)_ `_AdaptiveSignal`

### Functions
- *(none)*

### Other top-level statements
- import random
- import time
- import logging
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- from concept_store import ConceptStore, from concept_store import Concept, from concept_store import Relation
- from concept_extractor import ConceptExtractor
- from episodic_linker import EpisodicLinker
- from vector_store import VectorStore
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## memory/semantic_memory_manager.py

### Classes
- `MaintenancePlan`
- `MaintenanceOutcome`
- `SemanticMemoryManager`

### Functions
- _(private)_ `_normalise_snapshot`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional
- from concept_extractor import ConceptExtractor
- from summarizer import MemorySnapshot, from summarizer import ProgressiveSummarizer, from summarizer import SummarizationResult
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## memory/summarizer.py

### Classes
- `SummarizerConfig`
- `MemorySnapshot`
- `DigestDecision`
- `SummarizationResult`
- `SummarizationError`
- `ProgressiveSummarizer`

### Functions
- _(private)_ `_normalise_text`, `_normalise_string`, `_normalise_float`, `_normalise_tags`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## memory/vector_store.py

### Classes
- `VectorStore`
- _(private)_ `_MatchContext`, `_BoundedOnlineLinear`, `_DiscreteThompsonSampler`

### Functions
- _(private)_ `_clamp`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import random
- import time
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.core.config import cfg
- from AGI_Evolutive.memory.encoders import TinyEncoder, from AGI_Evolutive.memory.encoders import cosine as cosine_similarity
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_DIR`
- Assignment to `LOGGER`

## metacog/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from calibration import CalibrationMeter, from calibration import NoveltyDetector
- Assignment to `__all__`

## metacog/calibration.py

### Classes
- `OnlineLogisticRegressor`
- `LogisticCalibrator`
- `IsotonicCalibrator`
- `CompositeCalibrator`
- `OnlineTextNoveltyClassifier`
- `CalibrationMeter`
- `NoveltyDetector`

### Functions
- _(private)_ `_sigmoid`, `_safe_float`, `_extract_text`, `_calibration_features`, `_normalise_feature_vectors`

### Other top-level statements
- from __future__ import annotations
- from typing import Dict, from typing import Any, from typing import Optional, from typing import List, from typing import Tuple, from typing import Iterable, from typing import Callable
- import os, import json, import time, import uuid, import math, import re, import logging
- from collections import deque
- from statistics import mean
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `CalibFeatureFn`
- Assignment to `RE_TEXT_TOKEN`
- Assignment to `RE_HAS_EMOJI`
- Assignment to `_PUNCTUATION`
- from AGI_Evolutive.utils.jsonsafe import json_sanitize

## metacognition/__init__.py

### Classes
- `MetacognitiveState`
- `CognitiveDomain`
- `MetacognitiveEvent`
- `SelfModel`
- `ReflectionSession`
- `ThompsonBandit`
- `MetacognitiveSystem`
- `ErrorDetectionSystem`
- `BiasMonitoringSystem`
- `ResourceMonitoringSystem`
- `ProgressTrackingSystem`
- `StrategySelector`
- `MetacognitiveAttention`
- `EffortRegulator`
- `MetacognitiveGoalManager`

### Functions
- _(private)_ `_clip`

### Other top-level statements
- Module docstring
- import logging
- import numpy as np
- import time
- from datetime import datetime, from datetime import timedelta
- from typing import Dict, from typing import List, from typing import Any, from typing import Optional, from typing import Tuple, from typing import Set, from typing import Callable, from typing import Mapping, from typing import Sequence
- from dataclasses import dataclass, from dataclasses import field
- from enum import Enum
- import threading
- from collections import defaultdict, from collections import deque
- import math
- import json
- import inspect
- import re
- from AGI_Evolutive.cognition.meta_cognition import OnlineLinear
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from experimentation import MetacognitionExperimenter, from experimentation import calibrate_self_model
- Assignment to `LOGGER`
- Top-level if statement

## metacognition/experimentation.py

### Classes
- `Experiment`
- `MetacognitionExperimenter`

### Functions
- `calibrate_self_model`
- _(private)_ `_now`, `_ensure_dir`, `_adaptive_learning_rate`

### Other top-level statements
- from __future__ import annotations
- from typing import Dict, from typing import Any, from typing import Optional, from typing import Iterable, from typing import Mapping, from typing import Sequence
- from dataclasses import dataclass, from dataclasses import asdict, from dataclasses import field
- from collections import deque
- from copy import deepcopy
- import logging
- import random
- import statistics
- import json
- import os
- import time
- import uuid
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `EXPERIMENTS_LOG`
- Assignment to `ABILITY_TO_METRIC`
- Assignment to `PLAN_LIBRARY`

## models/__init__.py

### Classes
- *(none)*

### Functions
- `summarize_user_models`
- _(private)_ `_sorted_items`, `_sanitize_interactions`, `_extract_state`, `_build_llm_payload`, `_fallback_summary`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- from typing import Any, from typing import Callable, from typing import Iterable, from typing import Mapping, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from intent import IntentModel
- from user import UserModel
- Assignment to `LOGGER`
- Assignment to `__all__`

## models/intent.py

### Classes
- `Intent`
- `OnlineIntentClassifier`
- `IntentModel`

### Functions
- _(private)_ `_tokenize`, `_has_emoji`, `_text_features`

### Other top-level statements
- from __future__ import annotations
- import json
- import math
- import os
- import re
- import time
- from collections import defaultdict
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- import logging
- Assignment to `LOGGER`
- Top-level try block
- Top-level try block
- Assignment to `TTL_CANDIDATES`
- Assignment to `_WORD_PATTERN`

## models/user.py

### Classes
- `UserModel`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- from typing import Dict, from typing import Any, from typing import Optional, from typing import List
- import os, import json, import datetime as dt, import time, import math, import logging
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## orchestrator.py

### Classes
- `OnlinePlattCalibrator`
- `DiscreteThompsonSampler`
- `AdaptiveEMA`
- `OnlineBoundedLinear`
- `AdaptiveSJConfig`
- `FallbackIntentClassifier`
- `Orchestrator`
- _(private)_ `_MemoryStoreAdapter`, `_ConceptAdapter`, `_EpisodicAdapter`, `_ConsolidatorAdapter`, `_PerceptionAdapter`, `_ActionAdapter`, `_EmotionAdapter`, `_MetaAdapter`, `_HomeostasisAdapter`, `_ReflectionAdapter`, `_PlannerAdapter`, `_PolicyAdapter`, `_HabitAdapter`, `_EvolutionAdapter`

### Functions
- _(private)_ `_llm_enabled`, `_llm_manager`, `_get_process_memory_kb`, `_normalize_text`

### Other top-level statements
- import math
- import os
- import random
- import re
- import logging
- import statistics
- import threading
- import time
- import unicodedata
- from datetime import datetime, from datetime import timedelta
- from contextlib import nullcontext
- from types import SimpleNamespace
- from collections import deque, from collections import defaultdict
- from typing import Any, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Tuple, from typing import Mapping
- Top-level try block
- from AGI_Evolutive.cognition.context_inference import infer_where_and_apply
- from AGI_Evolutive.cognition.evolution_manager import EvolutionManager
- from AGI_Evolutive.cognition.habit_system import HabitRoutine, from AGI_Evolutive.cognition.habit_system import HabitSystem
- from AGI_Evolutive.cognition.homeostasis import Homeostasis
- from AGI_Evolutive.cognition.identity_mission import recommend_and_apply_mission
- from AGI_Evolutive.cognition.identity_principles import run_and_apply_principles
- from AGI_Evolutive.cognition.meta_cognition import MetaCognition
- from AGI_Evolutive.cognition.planner import Planner
- from AGI_Evolutive.cognition.proposer import Proposer
- from AGI_Evolutive.cognition.preferences_inference import apply_preferences_if_confident
- from AGI_Evolutive.cognition.reflection_loop import ReflectionLoop
- from AGI_Evolutive.cognition.thinking_monitor import ThinkingMonitor
- from AGI_Evolutive.cognition.trigger_bus import TriggerBus
- from AGI_Evolutive.cognition.trigger_router import TriggerRouter
- from AGI_Evolutive.cognition.understanding_aggregator import UnderstandingAggregator
- from AGI_Evolutive.cognition.pipelines_registry import PIPELINE_POLICY, from AGI_Evolutive.cognition.pipelines_registry import REGISTRY, from AGI_Evolutive.cognition.pipelines_registry import Stage, from AGI_Evolutive.cognition.pipelines_registry import ActMode, from AGI_Evolutive.cognition.pipelines_registry import should_skip_stage
- from AGI_Evolutive.core.config import load_config
- from AGI_Evolutive.core.decision_journal import DecisionJournal
- from AGI_Evolutive.core.evaluation import get_last_priority_token, from AGI_Evolutive.core.evaluation import unified_priority
- from AGI_Evolutive.core.reasoning_ledger import ReasoningLedger
- from AGI_Evolutive.core.policy import PolicyEngine
- from AGI_Evolutive.core.selfhood_engine import SelfhoodEngine
- from AGI_Evolutive.core.self_model import SelfModel
- from AGI_Evolutive.core.telemetry import Telemetry
- from AGI_Evolutive.core.timeline_manager import TimelineManager
- from AGI_Evolutive.core.trigger_types import Trigger, from AGI_Evolutive.core.trigger_types import TriggerType
- from AGI_Evolutive.emotions.emotion_engine import EmotionEngine
- from AGI_Evolutive.goals.curiosity import CuriosityEngine
- from AGI_Evolutive.io.action_interface import ActionInterface
- from AGI_Evolutive.io.intent_classifier import classify
- from AGI_Evolutive.io.perception_interface import PerceptionInterface
- from AGI_Evolutive.memory.concept_extractor import ConceptExtractor
- from AGI_Evolutive.memory.concept_store import ConceptStore
- from AGI_Evolutive.memory.consolidator import Consolidator
- from AGI_Evolutive.memory.episodic_linker import EpisodicLinker
- from AGI_Evolutive.memory.memory_store import MemoryStore
- from AGI_Evolutive.memory.semantic_bridge import SemanticMemoryBridge
- from AGI_Evolutive.light_scheduler import LightScheduler
- from AGI_Evolutive.runtime.job_manager import JobManager
- from AGI_Evolutive.runtime.phenomenal_kernel import ModeManager, from AGI_Evolutive.runtime.phenomenal_kernel import PhenomenalKernel
- from AGI_Evolutive.phenomenology import PhenomenalJournal, from AGI_Evolutive.phenomenology import PhenomenalQuestioner, from AGI_Evolutive.phenomenology import PhenomenalRecall
- from AGI_Evolutive.runtime.system_monitor import SystemMonitor
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled, from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `_DEFAULT_SJ_CONF`
- Assignment to `_DEFAULT_NEED_PROTOCOL`
- Assignment to `_NEED_PROTOCOLS`
- Assignment to `THREAT_PATTERN`

## perception/__init__.py

### Classes
- `OnlineLinear`
- `DiscreteThompsonSampler`
- `AdaptiveParameter`
- `AdaptiveParameterManager`
- `Modality`
- `FeatureType`
- `StructuralEvolutionManager`
- `PerceptualObject`
- `PerceptualScene`
- `PerceptionSystem`
- `VisualProcessor`
- `AuditoryProcessor`
- `TactileProcessor`
- `ProprioceptiveProcessor`
- `TemporalProcessor`
- `CrossModalBinder`
- `TemporalSync`
- `SpatialAligner`
- `ConfidenceCalibrator`
- `BottomUpSalience`
- `TopDownGuidance`
- `InhibitionOfReturn`
- `AttentionalBlink`
- `GestaltGrouper`

### Functions
- _(private)_ `_label_components`

### Other top-level statements
- Module docstring
- import hashlib
- import logging
- import math
- import time
- from collections import deque
- from datetime import datetime
- from dataclasses import dataclass
- from enum import Enum
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- import numpy as np
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Top-level if statement

## phenomenology/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from journal import PhenomenalEpisode, from journal import PhenomenalJournal, from journal import PhenomenalRecall, from journal import PhenomenalQuestioner
- Assignment to `__all__`

## phenomenology/journal.py

### Classes
- `PhenomenalEpisode`
- `PhenomenalJournal`
- `PhenomenalRecall`
- `PhenomenalQuestioner`

### Functions
- _(private)_ `_now`, `_safe_float`

### Other top-level statements
- from __future__ import annotations
- import json
- import os
- import threading
- import time
- import uuid
- from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Deque, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple

## planning/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from htn import HTNPlanner
- Assignment to `__all__`

## planning/htn.py

### Classes
- `HTNPlanner`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.reasoning.structures import HTNPlanner as _BasePlanner
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## reasoning/__init__.py

### Classes
- `ReasoningSystem`

### Functions
- _(private)_ `_normalise_mapping`, `_normalise_value`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import time
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional
- from AGI_Evolutive.utils.llm_service import get_llm_manager
- from strategies import ReasoningEpisodeDirective, from strategies import run_reasoning_episode
- Assignment to `__all__`

## reasoning/abduction.py

### Classes
- `Hypothesis`
- `AdaptiveTextClassifier`
- `AbductiveAdaptationManager`
- `AbductiveReasoner`
- `EntropyQuestionPolicy`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import TYPE_CHECKING, from typing import Any, from typing import Callable, from typing import Deque, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- import datetime as dt
- import logging
- import re
- from collections import defaultdict, from collections import deque
- from learning import OnlineLinearModel
- from utils.llm_service import try_call_llm_dict
- Assignment to `logger`
- Assignment to `FRENCH_CAUSE_REGEX`
- from structures import CausalStore, from structures import DomainSimulator, from structures import HTNPlanner, from structures import SimulationResult, from structures import TaskNode
- Top-level if statement

## reasoning/causal.py

### Classes
- `CounterfactualReport`
- `SCMStore`
- `CounterfactualSimulator`

### Functions
- _(private)_ `_truncate_text`, `_sanitize_payload`, `_coerce_float`, `_coerce_int`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import time
- from collections import deque
- from dataclasses import dataclass
- from typing import Any, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple, from typing import Union
- from utils.llm_service import try_call_llm_dict
- from structures import CausalStore, from structures import DomainSimulator, from structures import SimulationResult
- Assignment to `logger`
- Assignment to `_MAX_TEXT_LENGTH`
- Assignment to `_MAX_LIST_ITEMS`

## reasoning/question_engine.py

### Classes
- `QuestionEngine`

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import random
- from typing import TYPE_CHECKING, from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- Top-level try block
- Top-level if statement
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## reasoning/strategies.py

### Classes
- `ReasoningFailure`
- `ReasoningQuestion`
- `ReasoningAction`
- `ReasoningProposal`
- `ReasoningEpisodeDirective`

### Functions
- `run_reasoning_episode`
- _(private)_ `_normalise_text`, `_normalise_float`, `_normalise_sequence`, `_normalise_mapping`, `_normalise_value`, `_clamp_confidence`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## reasoning/structures.py

### Classes
- `Hypothesis`
- `Test`
- `Evidence`
- `Update`
- `CausalLink`
- `CausalStore`
- `SimulationResult`
- `DomainSimulator`
- `TaskNode`
- `HTNPlanner`

### Functions
- `now`
- `episode_record`
- `summary_record`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import time
- from dataclasses import asdict, from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional

## retrieval/adaptive_controller.py

### Classes
- `RAGOrchestrationError`
- `RAGPlanRequest`
- `RAGPlan`
- `RAGAdaptiveController`

### Functions
- _(private)_ `_coerce_string`, `_coerce_string_list`, `_coerce_mapping`, `_coerce_actions`, `_merge_nested`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## retrieval/rag5/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- from pipeline import RAGAnswer, from pipeline import RAGDocument, from pipeline import RAGPipeline, from pipeline import RAGPipelineError, from pipeline import RAGRequest
- Assignment to `__all__`

## retrieval/rag5/pipeline.py

### Classes
- `RAGPipelineError`
- `RAGDocument`
- `RAGRequest`
- `RAGAnswer`
- `RAGPipeline`

### Functions
- _(private)_ `_coerce_string`, `_coerce_mapping`, `_coerce_string_list`, `_ensure_documents`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import get_llm_manager
- Assignment to `__all__`

## runtime/__init__.py

### Classes
- *(none)*

### Functions
- *(none)*

### Other top-level statements
- Module docstring
- Assignment to `__all__`

## runtime/analytics.py

### Classes
- `EventPipeline`
- `RollingMetricAggregator`
- `SnapshotDriftTracker`
- `LLMAnalyticsInterpreter`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import hashlib
- import json
- import logging
- import os
- import queue
- import threading
- import time
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`

## runtime/dash.py

### Classes
- *(none)*

### Functions
- `read_jsonl`
- `read_json`
- `bar`
- `section`
- `parse_timestamp`
- `filter_since`
- `load_logs`
- `compute_reasoning_metrics`
- `compute_experiment_metrics`
- `compute_goal_metrics`
- `compute_insights`
- `format_metric`
- `render_reasoning_rows`
- `render_experiment_rows`
- `render_goal_rows`
- `console_once`
- `console_watch`
- `goal_token_matches`
- `apply_goal_filter_to_data`
- `build_html`
- `export_html`
- `serve_dashboard`

### Other top-level statements
- import argparse
- import json
- import logging
- import os
- import time
- from collections import Counter
- from datetime import datetime, from datetime import timedelta
- from html import escape
- from http.server import BaseHTTPRequestHandler, from http.server import ThreadingHTTPServer
- from statistics import mean
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional, from typing import Sequence
- from urllib.parse import parse_qs, from urllib.parse import urlparse
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `JSONLike`
- Assignment to `LOGGER`
- Top-level if statement

## runtime/job_manager.py

### Classes
- `Job`
- `JobContext`
- `JobManager`
- _(private)_ `_PQItem`, `_OnlinePriorityModel`

### Functions
- _(private)_ `_now`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Optional, from typing import List, from typing import Deque, from typing import Tuple
- from contextlib import contextmanager
- import time, import threading, import heapq, import os, import json, import uuid, import traceback, import collections, import math, import random, import logging
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## runtime/logger.py

### Classes
- `JSONLLogger`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import json
- import logging
- import os
- import threading
- import time
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Optional, from typing import TYPE_CHECKING
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from analytics import EventPipeline, from analytics import SnapshotDriftTracker
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level if statement
- Assignment to `logger`

## runtime/phenomenal_kernel.py

### Classes
- `SystemAlert`
- `PhenomenalKernel`
- `ModeManager`

### Functions
- _(private)_ `_clip`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import time
- from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Deque, from typing import Dict, from typing import Iterable, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `__all__`
- Assignment to `LOGGER`

## runtime/response.py

### Classes
- *(none)*

### Functions
- `humanize_reasoning_block`
- `ensure_contract`
- `format_agent_reply`
- _(private)_ `_llm_enabled`, `_llm_manager`, `_coerce_float`, `_coerce_list`, `_extract_str`, `_split_reasoning_bullets`, `_split_reasoning_segments`, `_llm_rewrite_reasoning`, `_stringify_list`, `_ensure_list`

### Other top-level statements
- from __future__ import annotations
- from typing import Any, from typing import Dict, from typing import List, from typing import Mapping, from typing import Optional, from typing import Tuple
- import logging
- import re
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`
- Assignment to `CONTRACT_KEYS`
- Assignment to `CONTRACT_DEFAULTS`

## runtime/scheduler.py

### Classes
- `AdaptiveTaskPolicy`
- `OnlineLogistic`
- `OnlinePlattCalibrator`
- `Scheduler`

### Functions
- _(private)_ `_now`, `_safe_json`, `_write_json`, `_append_jsonl`, `_clamp`

### Other top-level statements
- Module docstring
- import json
- import logging
- import math
- import os
- import random
- import threading
- import time
- import traceback
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Optional, from typing import Sequence
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.core.global_workspace import GlobalWorkspace
- from AGI_Evolutive.knowledge.mechanism_store import MechanismStore
- from AGI_Evolutive.cognition.principle_inducer import PrincipleInducer
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `logger`

## runtime/system_monitor.py

### Classes
- `DiskSnapshot`
- `SystemMonitor`

### Functions
- _(private)_ `_bytes_to_human`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import subprocess
- import time
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import Optional
- import psutil
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`

## self_improver/__init__.py

### Classes
- `SelfImprover`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import json
- import logging
- import os
- import time
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from metrics import aggregate_metrics, from metrics import bootstrap_superiority, from metrics import dominates
- from mutations import generate_overrides
- from promote import PromotionManager
- from sandbox import SandboxRunner, from sandbox import ArchFactory
- from quality import QualityGateRunner
- from code_evolver import CodeEvolver
- Assignment to `_LOGGER`

## self_improver/code_evolver.py

### Classes
- `CodePatch`
- `OnlineHeuristicLearner`
- `CodeEvolver`
- _(private)_ `_ScoreHeuristicTweaker`

### Functions
- _(private)_ `_extract_numeric_patch`

### Other top-level statements
- from __future__ import annotations
- import ast
- import contextlib
- import difflib
- import importlib
- import json
- import logging
- import re
- import random
- import shutil
- import tempfile
- import time
- import uuid
- from dataclasses import dataclass
- from pathlib import Path
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Optional
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from quality import QualityGateRunner
- Assignment to `logger`

## self_improver/metrics.py

### Classes
- `RunningMoments`
- `AdaptiveDominanceModel`

### Functions
- `aggregate_metrics`
- `dominates`
- `bootstrap_superiority`
- _(private)_ `_sigmoid`, `_clip`, `_llm_dominance_decision`, `_iter_metric_keys`, `_dominates_static`, `_pairwise_win_counts`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field
- from statistics import mean
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Tuple
- import logging
- import math
- import random
- from bisect import bisect_left, from bisect import bisect_right
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_LOGGER`
- Assignment to `_ADAPTIVE_MODEL`

## self_improver/mutations.py

### Classes
- _(private)_ `_KeyStats`, `_MutationMemory`

### Functions
- `generate_overrides`
- `record_feedback`
- `current_leaderboard`
- _(private)_ `_clip`, `_base_amplitude`, `_apply_llm_guidance`, `_probability_like`, `_mutate_value`

### Other top-level statements
- from __future__ import annotations
- import logging
- import math
- import random
- from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import MutableMapping, from typing import Sequence
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `DEFAULTS`
- Assignment to `_MEMORY`
- Assignment to `_LOGGER`

## self_improver/promote.py

### Classes
- `PromotionStorage`
- `PromotionError`
- `QualityGateOutcome`
- `CanaryDeployer`
- `PromotionManager`
- `PromoteManager`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import json
- import logging
- import os
- import time
- import uuid
- from dataclasses import dataclass
- from typing import Any, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Protocol, from typing import TYPE_CHECKING
- from AGI_Evolutive.core.structures.mai import MAI
- from AGI_Evolutive.knowledge.mechanism_store import MechanismStore
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Top-level if statement

## self_improver/quality.py

### Classes
- `GateResult`
- `QualityGateRunner`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import importlib
- import logging
- from dataclasses import dataclass
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Optional
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_LOGGER`

## self_improver/sandbox.py

### Classes
- `OnlineLogisticModel`
- `AdaptiveDecisionMaker`
- `DatasetRegistry`
- `SandboxRunner`
- _(private)_ `_SuiteState`

### Functions
- *(none)*

### Other top-level statements
- from __future__ import annotations
- import json
- import logging
- import math
- import os
- import random
- import time
- from dataclasses import dataclass, from dataclasses import field
- from statistics import mean, from statistics import pstdev
- from typing import Any, from typing import Callable, from typing import Dict, from typing import List, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- from metrics import aggregate_metrics
- Assignment to `ArchFactory`
- Assignment to `logger`

## self_improver/skill_acquisition.py

### Classes
- `SkillTrial`
- `SkillRequest`
- `SkillExecutionContext`
- `SkillSandboxManager`

### Functions
- _(private)_ `_now`, `_normalise_text`, `_unique_keywords`, `_coerce_bool`, `_first_text`

### Other top-level statements
- from __future__ import annotations
- import glob
- import json
- import os
- import logging
- import threading
- import time
- import uuid
- import weakref
- from collections import deque
- from dataclasses import dataclass, from dataclasses import field
- from pathlib import Path
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import List, from typing import Mapping, from typing import Optional, from typing import Sequence, from typing import Tuple
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `_LOGGER`
- Assignment to `OperationFunc`

## social/adaptive_lexicon.py

### Classes
- `OnlineLogisticCalibrator`
- `DiscreteThompsonSampler`
- `LexEntry`
- `ArchiveEntry`
- `AdaptiveLexicon`

### Functions
- `clamp`
- _(private)_ `_now`, `_strip_accents`, `_normalize`, `_ngrams`, `_tokenize`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field, from dataclasses import asdict
- from typing import Dict, from typing import Any, from typing import List, from typing import Optional, from typing import Tuple
- import re, import json, import os, import time, import math, import unicodedata, import random, import logging
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `_STOPWORDS`
- Assignment to `_EMOJI_RE`

## social/interaction_miner.py

### Classes
- `OnlineTextActClassifier`
- `OnlineScoreCalibrator`
- `DialogueTurn`
- `InteractionMiner`

### Functions
- `clamp`
- _(private)_ `_now`, `_hash`, `_strip_accents`, `_normalize`

### Other top-level statements
- from __future__ import annotations
- import logging
- from dataclasses import dataclass
- from typing import List, from typing import Dict, from typing import Any, from typing import Optional, from typing import Tuple
- import re
- import time
- import hashlib
- import math
- import unicodedata
- from collections import defaultdict
- from AGI_Evolutive.social.interaction_rule import InteractionRule, from AGI_Evolutive.social.interaction_rule import Predicate, from AGI_Evolutive.social.interaction_rule import TacticSpec, from AGI_Evolutive.social.interaction_rule import ContextBuilder
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- Assignment to `LOGGER`
- Assignment to `RE_QMARK`
- Assignment to `RE_COMPLIMENT`
- Assignment to `RE_THANKS`
- Assignment to `RE_DISAGREE`
- Assignment to `RE_EXPLAIN`
- Assignment to `RE_CONFUSED`
- Assignment to `RE_CLARIFY`
- Assignment to `RE_INSINUATE`
- Assignment to `RE_ACK`

## social/interaction_rule.py

### Classes
- `OnlineLinear`
- `AdaptiveEMA`
- `Predicate`
- `TacticSpec`
- `EffectPosterior`
- `InteractionRule`
- `ContextBuilder`

### Functions
- `clamp`
- `make_rule_insinuation_banter`
- _(private)_ `_now`, `_hash`

### Other top-level statements
- from __future__ import annotations
- from dataclasses import dataclass, from dataclasses import field, from dataclasses import asdict
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- import time, import math, import hashlib, import json, import logging
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `TS`

## social/social_critic.py

### Classes
- `ContextualWeightLearner`
- `SocialCritic`

### Functions
- _(private)_ `_now`, `_contains_any`, `_sentiment_heuristic`, `_acceptance_marker`, `_relationship_signal`

### Other top-level statements
- from __future__ import annotations
- from typing import Any, from typing import Dict, from typing import Optional, from typing import List, from typing import Tuple
- import time, import json, import random, import re, import logging
- from collections import deque
- from AGI_Evolutive.social.adaptive_lexicon import AdaptiveLexicon
- from AGI_Evolutive.social.interaction_rule import InteractionRule, from AGI_Evolutive.social.interaction_rule import clamp
- from AGI_Evolutive.utils.llm_service import try_call_llm_dict
- Assignment to `LOGGER`
- Assignment to `POS_MARKERS`
- Assignment to `NEG_MARKERS`
- Assignment to `ACCEPTANCE`
- Assignment to `REL_PRONOUNS`
- Assignment to `REL_KEYWORDS`
- Assignment to `REL_QUESTIONS`
- Assignment to `REL_DISCLOSURE`

## social/tactic_selector.py

### Classes
- `FullLinUCB`
- `OnlineLogisticWeights`
- `DiagLinUCB`
- `TacticSelector`
- `StyleMacroBandit`
- _(private)_ `_ThompsonBandit`

### Functions
- _(private)_ `_now`

### Other top-level statements
- from __future__ import annotations
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- from collections import defaultdict
- import logging
- import time, import math, import random
- import numpy as np
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled
- from AGI_Evolutive.social.interaction_rule import InteractionRule, from AGI_Evolutive.social.interaction_rule import ContextBuilder, from AGI_Evolutive.social.interaction_rule import Predicate, from AGI_Evolutive.social.interaction_rule import TacticSpec, from AGI_Evolutive.social.interaction_rule import clamp
- Assignment to `LOGGER`
- Assignment to `_DEFAULT_CFG`

## utils/__init__.py

### Classes
- *(none)*

### Functions
- `now_iso`
- `safe_write_json`

### Other top-level statements
- import datetime
- import json
- import os
- from typing import Any
- from AGI_Evolutive.utils.jsonsafe import json_sanitize
- from AGI_Evolutive.utils.llm_client import JSON_ONLY_DIRECTIVE, from AGI_Evolutive.utils.llm_client import LLMCallError, from AGI_Evolutive.utils.llm_client import LLMResult, from AGI_Evolutive.utils.llm_client import OllamaLLMClient, from AGI_Evolutive.utils.llm_client import OllamaModelConfig, from AGI_Evolutive.utils.llm_client import build_json_prompt
- from AGI_Evolutive.utils.llm_service import LLMIntegrationError, from AGI_Evolutive.utils.llm_service import LLMIntegrationManager, from AGI_Evolutive.utils.llm_service import LLMInvocation, from AGI_Evolutive.utils.llm_service import LLMUnavailableError, from AGI_Evolutive.utils.llm_service import get_llm_manager, from AGI_Evolutive.utils.llm_service import is_llm_enabled, from AGI_Evolutive.utils.llm_service import set_llm_manager
- from AGI_Evolutive.utils.llm_specs import AVAILABLE_MODELS, from AGI_Evolutive.utils.llm_specs import LLMIntegrationSpec, from AGI_Evolutive.utils.llm_specs import LLM_INTEGRATION_SPECS, from AGI_Evolutive.utils.llm_specs import SPEC_BY_KEY, from AGI_Evolutive.utils.llm_specs import get_spec
- Assignment to `__all__`

## utils/jsonsafe.py

### Classes
- *(none)*

### Functions
- `json_sanitize`

### Other top-level statements
- import datetime
- import pathlib
- from typing import Any

## utils/llm_client.py

### Classes
- `OllamaModelConfig`
- `LLMResult`
- `LLMCallError`
- `OllamaLLMClient`

### Functions
- `build_json_prompt`
- _(private)_ `_json_default`, `_ensure_text`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import json
- import logging
- import socket
- from dataclasses import asdict, from dataclasses import dataclass, from dataclasses import is_dataclass
- from enum import Enum
- from typing import Any, from typing import Callable, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from urllib import error as urlerror
- from urllib import request as urlrequest
- Assignment to `JSON_ONLY_DIRECTIVE`
- Assignment to `TransportCallable`
- Assignment to `__all__`

## utils/llm_contracts.py

### Classes
- *(none)*

### Functions
- `enforce_llm_contract`
- _(private)_ `_as_text`, `_as_float`, `_clip_unit`, `_iter_sequence`, `_sanitize_dialogue_state`, `_sanitize_episodic_linker`, `_sanitize_identity_mission`, `_sanitize_goal_interpreter`, `_sanitize_trigger_router`, `_sanitize_planner_support`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from typing import Any, from typing import Callable, from typing import Dict, from typing import Iterable, from typing import Mapping, from typing import Optional
- Assignment to `Sanitizer`
- Assignment to `_SANITIZERS`
- Assignment to `__all__`

## utils/llm_service.py

### Classes
- `LLMIntegrationError`
- `LLMUnavailableError`
- `LLMInvocation`
- `LLMCallRecord`
- `LLMIntegrationManager`

### Functions
- `get_recent_llm_activity`
- `get_llm_manager`
- `set_llm_manager`
- `is_llm_enabled`
- `try_call_llm_dict`
- _(private)_ `_env_flag`, `_llm_env_enabled`, `_record_activity`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import os
- import threading
- import time
- from collections import deque
- from dataclasses import dataclass
- from typing import Any, from typing import Mapping, from typing import MutableMapping, from typing import Optional, from typing import Sequence
- from itertools import islice
- from llm_client import LLMCallError, from llm_client import LLMResult, from llm_client import OllamaLLMClient, from llm_client import OllamaModelConfig
- from llm_specs import LLMIntegrationSpec, from llm_specs import get_spec
- Assignment to `_module_logger`
- Assignment to `_DEFAULT_ENABLED`
- Assignment to `_ACTIVITY_LOG`
- Assignment to `_default_manager`
- Assignment to `_default_lock`
- Assignment to `__all__`

## utils/llm_specs.py

### Classes
- `LLMIntegrationSpec`

### Functions
- `get_spec`
- _(private)_ `_spec`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- from dataclasses import dataclass
- from typing import Any, from typing import Iterable, from typing import Mapping, from typing import Sequence
- from llm_client import build_json_prompt
- Assignment to `AVAILABLE_MODELS`
- Assignment to `LLM_INTEGRATION_SPECS`
- Assignment to `SPEC_BY_KEY`
- Assignment to `__all__`

## utils/logging_setup.py

### Classes
- *(none)*

### Functions
- `configure_logging`
- _(private)_ `_resolve_level`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import os
- import sys
- from logging.handlers import RotatingFileHandler
- from pathlib import Path
- from typing import Optional
- Assignment to `_DEFAULT_LOG_PATH`
- Assignment to `_CONFIGURED_PATH`
- Assignment to `__all__`

## world_model/__init__.py

### Classes
- `DiscreteThompsonSampler`
- `BoundedOnlineLinear`
- `Node2D`
- `Edge`
- `SpatialReasoning`
- `TimeWindow`
- `TemporalReasoning`
- `Agent`
- `SocialModel`
- `Body`
- `PhysicsEngine`

### Functions
- _(private)_ `_now`, `_clamp`, `_mean`

### Other top-level statements
- Module docstring
- from __future__ import annotations
- import logging
- import math
- import time
- import random
- from collections.abc import Iterable, from collections.abc import Mapping, from collections.abc import Sequence
- from dataclasses import dataclass, from dataclasses import field
- from typing import Any, from typing import Dict, from typing import List, from typing import Optional, from typing import Tuple
- Top-level try block
- Assignment to `logger`
- Assignment to `__all__`
