# src/gate/gate_controller.py
"""
GateController - canonical enforcement wrapper.

Returns decision dict:
{
  "action": "OPEN"|"THROTTLE"|"HARD_LOCK",
  "diagnostics": {...},
  "receipt": {"payload": {...}, "signature": "<hex>"}
}
"""

import time
from typing import Dict, Any, Optional
from src.infra.crypto_signer import CryptoSigner

class GateController:
    """
    Minimal GateController for deterministic tests.
    Uses >= for threshold boundary checks (so threshold==0 forces lock).
    """

    def __init__(self, signer: Optional[CryptoSigner] = None, thresholds: Optional[Dict[str, float]] = None):
        self.signer = signer or CryptoSigner()
        # Default thresholds (placeholders)
        self.thresholds = thresholds or {"jsd_global_95": 0.5, "jsd_global_99": 0.8}

    def _decide(self, diagnostics: Dict[str, float]) -> str:
        """Use >= for decision boundaries (deterministic, explicit)."""
        jsd = float(diagnostics.get("jsd_global", 0.0))
        if jsd >= float(self.thresholds.get("jsd_global_99", 1e9)):
            return "HARD_LOCK"
        if jsd >= float(self.thresholds.get("jsd_global_95", 1e9)):
            return "THROTTLE"
        return "OPEN"

    def execute_pricing_action(self, action_type: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a governed action (entrypoint).
        context may contain diagnostic values (e.g., {"jsd_global": 0.92})
        Returns: {"action":..., "diagnostics":..., "receipt": {"payload":..., "signature": "<hex>"}}
        """
        diagnostics = {"jsd_global": float(context.get("jsd_global", 0.0))}
        action = self._decide(diagnostics)

        receipt_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action_type": action_type,
            "payload": payload,
            "action": action,
            "diagnostics": diagnostics
        }

        # Sign receipt payload (CryptoSigner accepts dict and will canonicalize)
        sig = self.signer.sign(receipt_payload)
        receipt = {"payload": receipt_payload, "signature": sig}

        return {"action": action, "diagnostics": diagnostics, "receipt": receipt}
