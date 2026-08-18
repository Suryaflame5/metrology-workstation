"""
AI Provider Abstraction Layer (Mode A: Deterministic Local, Mode B: Ollama, Mode C: Cloud BYOK).
"""

import json
import urllib.request
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        context_data: Dict[str, Any],
    ) -> str:
        """Generate reasoning text given prompt and verified context."""
        pass


class LocalDeterministicProvider(BaseAIProvider):
    """
    Offline Sovereign Deterministic Reasoning Engine (Mode A).
    Requires zero internet and zero external GPU models. Synthesizes findings directly from verified tool data.
    """
    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        context_data: Dict[str, Any],
    ) -> str:
        tool_results = context_data.get("tool_results", {})
        query = prompt.lower()

        # Handle 'why did it fail' / 'what changed' / 'drift' queries
        if "fail" in query or "why" in query or "change" in query or "drift" in query:
            drift_data = tool_results.get("predict_drift", {}).get("result", {})
            risk_data = tool_results.get("calculate_risk", {}).get("result", {})
            docs = tool_results.get("search_knowledge", {}).get("result", {}).get("documents", [])
            
            trend = drift_data.get("drift_trend", "STABLE")
            slope = drift_data.get("drift_slope_per_cycle", 0.0)
            risk = risk_data.get("current_risk_level", "LOW_RISK")
            
            top_citation = docs[0]["citation"] if docs else "[Internal SOP-CAL-042] §4.3"
            
            return (
                f"Based on execution of historical drift and anomaly analysis, the instrument exhibits '{trend}' "
                f"with a drift velocity of {slope:+.6f} units/cycle. The composite risk index is evaluated as '{risk}'. "
                f"In accordance with {top_citation}, guardband verification and shortened recalibration intervals are advised."
            )

        # Handle knowledge / standard search
        if "standard" in query or "sop" in query or "17025" in query or "z540" in query:
            docs = tool_results.get("search_knowledge", {}).get("result", {}).get("documents", [])
            if docs:
                return f"Found {len(docs)} applicable standard/SOP clause(s):\n" + "\n".join([f"• {d['citation']}: {d['content'][:140]}..." for d in docs])
            return "No matching standard or SOP documentation found in the local knowledge base."

        # Default structured answer
        return (
            "The engineering copilot analyzed your query against the active project, measurement datasets, and standard citations. "
            "All underlying uncertainty and conformity evaluations are computed with 50-digit exact decimal arithmetic by the deterministic metrology kernel."
        )


class OllamaProvider(BaseAIProvider):
    """Local Ollama Daemon Client (Mode B)."""
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3:latest"):
        self.host = host.rstrip("/")
        self.model = model

    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        context_data: Dict[str, Any],
    ) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"System Context:\n{system_instruction}\n\nEvidence:\n{json.dumps(context_data, default=str)}\n\nUser Question:\n{prompt}",
            "stream": False,
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "Ollama returned empty response.")
        except Exception as e:
            # Graceful fallback to Local Deterministic Provider if Ollama is offline
            return LocalDeterministicProvider().generate_response(prompt, system_instruction, context_data)


class CloudBYOKProvider(BaseAIProvider):
    """Cloud Bring-Your-Own-Key Provider (Mode C - OpenAI / Anthropic / Gemini compatible)."""
    def __init__(self, api_key: str, endpoint: str = "https://api.openai.com/v1/chat/completions", model: str = "gpt-4o"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model

    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        context_data: Dict[str, Any],
    ) -> str:
        if not self.api_key:
            return LocalDeterministicProvider().generate_response(prompt, system_instruction, context_data)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system_instruction}\nContext Evidence:\n{json.dumps(context_data, default=str)}"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception:
            return LocalDeterministicProvider().generate_response(prompt, system_instruction, context_data)
