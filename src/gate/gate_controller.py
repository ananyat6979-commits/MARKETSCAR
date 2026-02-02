from __future__ import annotations
import time
from typing import Dict, Any
from src.utils.canonical import canonical_bytes
from src.infra.crypto_signer import CryptoSigner

class GateController:
    """
    Minimal GateController implementation for tests.
    Real diagnostics will plug into `diagnostics` and thresholds.
    """

    def __init__(self, signer: CryptoSigner | None = None, thresholds: Dict[str, float] | None = None):
        self.signer = signer or CryptoSigner()
        # default conservative thresholds (placeholders)
        self.thresholds = thresholds or {"jsd_global_95": 0.5, "jsd_global_99": 0.8}

    def _decide(self, diagnostics: Dict[str, float]) -> str:
        """Deterministic policy: checks jsd_global against thresholds."""
        jsd = float(diagnostics.get("jsd_global", 0.0))
        if jsd > float(self.thresholds.get("jsd_global_99", 1e9)):
            return "HARD_LOCK"
        if jsd > float(self.thresholds.get("jsd_global_95", 1e9)):
            return "THROTTLE"
        return "OPEN"

    def execute_pricing_action(self, action_type: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper entrypoint for governed actions.
        Returns a dict with keys: action, diagnostics, receipt
        Receipt: { payload: {...}, signature: "<hex>" }
        """
        # diagnostics should be computed from context; tests can set context["jsd_global"]
        diagnostics = {"jsd_global": float(context.get("jsd_global", 0.0))}
        action = self._decide(diagnostics)

        receipt_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action_type": action_type,
            "payload": payload,
            "action": action,
            "diagnostics": diagnostics
        }

        # canonicalize and sign
        sig = self.signer.sign(receipt_payload)
        receipt = {"payload": receipt_payload, "signature": sig}

        decision = {"action": action, "diagnostics": diagnostics, "receipt": receipt}
        return decision
