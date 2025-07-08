"""Auto-Hypothesis Agent package.

모듈별 기능은 단계적으로 구현될 예정입니다.
"""

__all__ = []

"""Compatibility patch for PyTorch >=2.2 where torch.serialization.MAP_LOCATION was removed.
This constant is still imported by external libraries such as Pyro. To avoid an
ImportError when those libraries are imported, we monkey-patch the attribute
back onto ``torch.serialization`` if it is missing. The value assigned here is
only used for type-checking purposes inside those libraries, so a faithful type
alias definition is sufficient.
"""

# NOTE: This import must run *before* any third-party libraries (e.g. ``pyro``)
# attempt to import ``MAP_LOCATION`` from ``torch.serialization``. Since this
# package's ``__init__`` is executed very early (when the user script imports
# ``auto_hypothesis_agent``), placing the patch here guarantees the attribute
# is available in time.

from typing import Any, Callable, Optional, Union

import torch


# Older versions of PyTorch (<2.2) exposed the typing alias ``MAP_LOCATION``
# directly from ``torch.serialization``. Newer versions removed it, which breaks
# libraries that still rely on the old import path. We restore the attribute
# only if it is absent.

if not hasattr(torch.serialization, "MAP_LOCATION"):
    from torch import Tensor, device  # noqa: F401

    # Re-create the original typing alias. The exact signature is not critical
    # for runtime execution as it is primarily used for static typing, but we
    # replicate it for completeness.
    MAP_LOCATION = Optional[Union[str, "device", Callable[[Tensor, Any], Tensor]]]

    # Attach to the torch.serialization module so that downstream imports
    # ``from torch.serialization import MAP_LOCATION`` succeed.
    setattr(torch.serialization, "MAP_LOCATION", MAP_LOCATION)

# -----------------------------------------------------------------------------
# torch.optim.lr_scheduler compatibility (PyTorch < 2.3)
# -----------------------------------------------------------------------------
# In recent PyTorch versions (>=2.3), the internal class ``_LRScheduler`` was
# renamed and re-exported as ``LRScheduler``.  Some libraries (e.g., ``pyro``)
# depend on this new public alias.  When running with earlier versions that
# only provide ``_LRScheduler``, we create the missing alias so that
# ``torch.optim.lr_scheduler.LRScheduler`` resolves correctly.

try:
    from torch.optim import lr_scheduler as _lr_sched_mod  # noqa: N812  (alias)

    if not hasattr(_lr_sched_mod, "LRScheduler") and hasattr(
        _lr_sched_mod, "_LRScheduler"
    ):
        _lr_sched_mod.LRScheduler = _lr_sched_mod._LRScheduler  # type: ignore[attr-defined]
except ImportError:
    # Extremely unlikely: torch is not fully installed, in which case there
    # are bigger issues; ignore.
    pass 