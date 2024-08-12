from dataclasses import dataclass
from typing import Any, Dict

from pystratum_common.loader.helper.DocBlockHelper import DocBlockHelper
from pystratum_common.loader.helper.PlaceholderHelper import PlaceholderHelper
from pystratum_common.loader.helper.StoredRoutineHelper import StoredRoutineHelper
from pystratum_common.loader.helper.TypeHintHelper import TypeHintHelper


@dataclass
class LoaderContext:
    """
    The build context for loading stored routines.
    """
    # ------------------------------------------------------------------------------------------------------------------
    stored_routine: StoredRoutineHelper
    type_hints: TypeHintHelper
    doc_block: DocBlockHelper
    placeholders: PlaceholderHelper
    old_rdbms_metadata: Dict[str, Any]
    old_pystratum_metadata: Dict[str, Any]
    new_pystratum_metadata: Dict[str, Any]

# ----------------------------------------------------------------------------------------------------------------------
