import httpx
import json
import time
import os
import re
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, List, TypeVar, Union, Type, Literal
from pydantic import BaseModel, ValidationError
from src.config import logger, OLLAMA_HOST, OLLAMA_MODEL
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar('T', bound=Union[BaseModel, str])

INFERENCE_TIMEOUT = 20.0

SUPPORTED_DSL_ACTIONS = {"OPEN_URL", "SEARCH_WIKIPEDIA", "EXTRACT_FIRST_PARAGRAPH", "SAVE_MARKDOWN", "WAIT_SHORT", "DONE"}
MIN_WAIT_SECONDS = 1.0
MAX_WAIT_SECONDS = 5.0
MIN_ARTICLE_WORDS = 25


class SimpleActionDSL(BaseModel):
    action: Literal["OPEN_URL", "SEARCH_WIKIPEDIA", "EXTRACT_FIRST_PARAGRAPH", "SAVE_MARKDOWN", "WAIT_SHORT", "DONE"]
    url: Optional[str] = None
    query: Optional[str] = None
    content: Optional[str] = None
    seconds: Optional[float] = None
    summary: Optional[str] = None
    success: Optional[bool] = None


DSL_SYNONYMS = {
    "navigate": "OPEN_URL",
    "navigate_to": "OPEN_URL",
    "load_url": "OPEN_URL",
    "open_url": "OPEN_URL",
    "search": "SEARCH_WIKIPEDIA",
    "navigate_to_search": "SEARCH_WIKIPEDIA",
    "navigate to search bar": "SEARCH_WIKIPEDIA",
    "navigate_to_search_bar": "SEARCH_WIKIPEDIA",
    "extract": "EXTRACT_FIRST_PARAGRAPH",
    "extract_text": "EXTRACT_FIRST_PARAGRAPH",
    "extract_first_paragraph": "EXTRACT_FIRST_PARAGRAPH",
    "save_paragraph": "SAVE_MARKDOWN",
    "save_extracted_info": "SAVE_MARKDOWN",
    "save_extracted": "SAVE_MARKDOWN",
    "save_file": "SAVE_MARKDOWN",
    "save": "SAVE_MARKDOWN",
    "save_markdown": "SAVE_MARKDOWN",
    "wait": "WAIT_SHORT",
    "wait_short": "WAIT_SHORT",
    "scroll_down": "EXTRACT_FIRST_PARAGRAPH",
    "scroll_to_element": "EXTRACT_FIRST_PARAGRAPH",
    "done": "DONE",
}

BANNER_HINTS = (
    "wikidata contest",
    "contest/submission",
    "wikimedia foundation",
    "foundation, inc.",
    "donate to wikipedia",
    "temporary account",
)

class OllamaProvider:
    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip('/')
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(INFERENCE_TIMEOUT, connect=10.0))

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"num_gpu": 1, "temperature": 0.0}
        }

        try:
            logger.info(f"[CHECKPOINT] Sending generate request to Ollama (timeout: {INFERENCE_TIMEOUT}s)")
            start = time.time()
            response = await self.client.post(url, json=payload)
            latency_ms = (time.time() - start) * 1000
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "")

            os.makedirs("logs", exist_ok=True)
            log_file = f"logs/ollama_raw_{int(time.time())}.json"
            with open(log_file, 'w') as f:
                json.dump({"type": "generate", "prompt": prompt[:500], "response": data, "latency_ms": latency_ms}, f, indent=2)

            logger.info(f"[CHECKPOINT] Ollama generate response received. Latency: {latency_ms:.2f}ms")
            return content
        except httpx.TimeoutException:
            logger.error(f"[TIMEOUT] Ollama generate timed out after {INFERENCE_TIMEOUT}s")
            raise
        except Exception as e:
            logger.error(f"Ollama direct failed: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            models = [m['name'] for m in response.json().get('models', [])]
            return {"status": "healthy" if self.model in models or f"{self.model}:latest" in models else "model_missing"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def close(self):
        await self.client.aclose()

class OllamaLLM:
    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_HOST):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(INFERENCE_TIMEOUT, connect=10.0))
        self._inference_count = 0
        self._last_response_hash = None
        self._dsl_parse_failures = 0
        self._runtime_memory = {
            "current_url": "",
            "completed_goals": [],
            "last_actions": [],
            "repeated_actions": {},
            "extracted_data_status": False,
            "extracted_text": "",
            "file_saved": False,
            "stalled_count": 0,
            "last_url_for_action": "",
            "expected_query": "",
            "expected_file": "ai_summary.md",
            "visited_urls": {},
            "phase": "NAVIGATE",
            "save_action_dispatched": False,
        }
        os.makedirs("logs/dsl_outputs", exist_ok=True)

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    def _extract_json_object(self, content: str) -> Dict[str, Any]:
        """Extract first JSON object from text and parse it."""
        try:
            return json.loads(content)
        except Exception:
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in model output.")
            return json.loads(match.group(1))

    def _validate_dsl(self, payload: Dict[str, Any]) -> SimpleActionDSL:
        for fld in ("query", "content", "summary"):
            val = payload.get(fld)
            if isinstance(val, (int, float)):
                payload[fld] = str(val)
        action_value = payload.get("action")
        if isinstance(action_value, str):
            normalized = DSL_SYNONYMS.get(action_value.strip().lower(), action_value.strip().upper())
            payload["action"] = normalized
        if "text" in payload and "query" not in payload:
            payload["query"] = payload.get("text")
        if "target" in payload and not payload.get("query"):
            payload["query"] = payload.get("target")
        if "target" in payload and not payload.get("content"):
            payload["content"] = payload.get("target")
        dsl = SimpleActionDSL.model_validate(payload)
        if dsl.action not in SUPPORTED_DSL_ACTIONS:
            raise ValueError(f"Unsupported DSL action: {dsl.action}")

        if dsl.action == "OPEN_URL" and not dsl.url:
            dsl.url = "https://wikipedia.org"
        if dsl.action == "SEARCH_WIKIPEDIA" and not dsl.query:
            dsl.query = self._runtime_memory["expected_query"] or "Artificial Intelligence"
        if dsl.action == "SAVE_MARKDOWN":
            if not dsl.content:
                dsl.content = self._runtime_memory["extracted_text"]
            elif dsl.content and self._candidate_paragraph_ok(str(dsl.content).strip()):
                self._runtime_memory["extracted_text"] = str(dsl.content).strip()
                self._runtime_memory["extracted_data_status"] = True
        if dsl.action == "DONE" and not dsl.summary:
            dsl.summary = "Task completed."
        if dsl.action == "WAIT_SHORT":
            dsl.seconds = self._clamp_wait(dsl.seconds)
        if (
            dsl.action == "EXTRACT_FIRST_PARAGRAPH"
            and dsl.content
            and self._candidate_paragraph_ok(str(dsl.content).strip())
        ):
            self._runtime_memory["extracted_text"] = str(dsl.content).strip()
            self._runtime_memory["extracted_data_status"] = True
        return dsl

    def _coerce_action_payload(self, payload: Dict[str, Any]) -> None:
        raw = payload.get("action")
        if not isinstance(raw, str):
            return
        k = re.sub(r"\s+", " ", raw.strip().lower())
        if k in DSL_SYNONYMS:
            payload["action"] = DSL_SYNONYMS[k]
            return
        k2 = k.replace(" ", "_")
        if k2 in DSL_SYNONYMS:
            payload["action"] = DSL_SYNONYMS[k2]
            return

        phase = self._runtime_memory.get("phase") or self._phase_for_state()
        fallback = {
            "NAVIGATE": "OPEN_URL",
            "SEARCH": "SEARCH_WIKIPEDIA",
            "EXTRACT": "EXTRACT_FIRST_PARAGRAPH",
            "SAVE": "SAVE_MARKDOWN",
            "COMPLETE": "DONE",
        }.get(phase, "WAIT_SHORT")
        logger.warning(f"[ACTION_COERCE] Unknown action {raw!r} -> {fallback} (phase={phase})")
        payload["action"] = fallback

    def _markdown_output_ok(self) -> bool:
        path = self._runtime_memory.get("expected_file") or "ai_summary.md"
        path = path.replace("./", "")
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "r") as fh:
                body = fh.read().strip()
        except OSError:
            return False
        return self._candidate_paragraph_ok(body)

    def _try_deterministic_agent_step(
        self, output_format: Type[Any], inference_num: int
    ) -> Optional[ChatInvokeCompletion[Any]]:
        mem = self._runtime_memory

        gate_save = (
            not mem.get("file_saved")
            and not mem.get("save_action_dispatched")
            and bool((mem.get("expected_file") or "").strip())
            and self._candidate_paragraph_ok((mem.get("extracted_text") or "").strip())
            and "wikipedia.org/wiki/" in (mem.get("current_url") or "").lower()
        )
        gate_done = mem.get("file_saved") and self._markdown_output_ok()

        dsl: SimpleActionDSL | None = None
        if gate_save:
            dsl = SimpleActionDSL(
                action="SAVE_MARKDOWN",
                content=mem.get("extracted_text") or "",
            )
        elif gate_done:
            dsl = SimpleActionDSL(
                action="DONE",
                summary="Saved article paragraph to markdown (runtime-validated).",
                success=True,
            )

        if dsl is None:
            return None

        try:
            dsl = self._apply_guardrails(dsl)
            translated_action = self._translate_dsl_to_browser_action(dsl)
            self._track_progress(dsl)
            self._log_dsl_event(inference_num, "DETERMINISTIC_AGENT_STEP", dsl.model_dump())
            self._log_dsl_event(inference_num, "TRANSLATED_ACTION", translated_action)
            agent_output_json = self._build_agent_output_json(translated_action, dsl)
            completion = output_format.model_validate_json(agent_output_json)
        except Exception as e:
            logger.warning(f"[DETERMINISTIC_AGENT_STEP] Fallback to LLM: {e}")
            return None

        zero = ChatInvokeUsage(
            prompt_tokens=0,
            prompt_cached_tokens=0,
            prompt_cache_creation_tokens=0,
            prompt_image_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )
        return ChatInvokeCompletion(completion=completion, usage=zero, stop_reason="stop")

    def _clamp_wait(self, seconds: Optional[float]) -> float:
        val = seconds if seconds is not None else MIN_WAIT_SECONDS
        clamped = min(MAX_WAIT_SECONDS, max(MIN_WAIT_SECONDS, float(val)))
        if clamped != float(val):
            logger.warning(f"[WAIT_CLAMPED] Requested wait {val}s -> clamped to {clamped}s")
            self._log_dsl_event(self._inference_count, "WAIT_CLAMPED", {"requested_seconds": val, "clamped_seconds": clamped})
        return clamped

    def _extract_url_from_messages(self, messages: List[BaseMessage]) -> str:
        for msg in reversed(messages):
            content = getattr(msg, "content", "")
            text = str(content)
            matches = re.findall(r"https?://[^\s\]\)\"']+", text)
            if matches:
                return matches[-1].rstrip(".,")
        return self._runtime_memory["current_url"]

    def _extract_expected_query(self, messages: List[BaseMessage]) -> str:
        for msg in reversed(messages):
            text = str(getattr(msg, "content", ""))
            m = re.search(r"search for ([^,\n\.]+)", text, re.IGNORECASE)
            if m:
                return m.group(1).strip(" '\"")
        return self._runtime_memory["expected_query"]

    def _extract_expected_file(self, messages: List[BaseMessage]) -> str:
        for msg in reversed(messages):
            text = str(getattr(msg, "content", ""))
            m = re.search(r"([A-Za-z0-9_.-]+\.md)", text)
            if m:
                return m.group(1)
        return self._runtime_memory["expected_file"]

    def _word_count(self, text: str) -> int:
        if not text or not text.strip():
            return 0
        return len(re.findall(r"[A-Za-z0-9'_-]+", text))

    def _looks_like_banner_noise(self, text: str) -> bool:
        low = (text or "").lower()
        return any(h in low for h in BANNER_HINTS)

    def _candidate_paragraph_ok(self, candidate: str) -> bool:
        if not candidate or self._looks_like_selector(candidate):
            return False
        if re.search(r"<[a-zA-Z!/]", candidate):
            return False
        if any(tok in candidate for tok in ("<agent_", "</agent_", "<user_request", "</user_request>", "agent_history")):
            return False
        wc = self._word_count(candidate)
        if wc < MIN_ARTICLE_WORDS:
            return False
        if self._looks_like_banner_noise(candidate):
            return False
        return True

    def _extract_read_state_blocks(self, text: str) -> List[str]:
        return re.findall(r"<read_state_\d+>\s*(.*?)\s*</read_state_\d+>", text, re.DOTALL | re.IGNORECASE)

    def _extract_paragraph_text(self, messages: List[BaseMessage]) -> str:
        """Hydrate extraction only from evaluate/read_state payloads — never free-form UI transcript."""
        for msg in reversed(messages):
            text = str(getattr(msg, "content", ""))
            for block in self._extract_read_state_blocks(text):
                cand = re.sub(r"\s+", " ", block).strip()
                if self._candidate_paragraph_ok(cand):
                    return cand
            rd = re.search(
                r"(?im)^Result\s*\n(.{200,}?)(?=\n\n|\n[A-Z][a-z]+\n|\Z)",
                text,
                re.DOTALL,
            )
            if rd:
                cand = re.sub(r"\s+", " ", rd.group(1)).strip()
                if self._candidate_paragraph_ok(cand):
                    return cand
            summary_json = re.search(r'"Summary"\s*:\s*"([^"]+)"', text)
            if summary_json:
                cand = summary_json.group(1).strip()
                if self._candidate_paragraph_ok(cand):
                    return cand
            extract_json = re.search(r'"extract"\s*:\s*"([^"]+)"', text)
            if extract_json:
                cand = extract_json.group(1).strip()
                if self._candidate_paragraph_ok(cand):
                    return cand
            result_block = re.search(r"<result>\s*(.*?)\s*</result>", text, re.DOTALL)
            if result_block:
                cand = re.sub(r"\s+", " ", result_block.group(1)).strip()
                if self._candidate_paragraph_ok(cand):
                    return cand
        return self._runtime_memory["extracted_text"]

    def _search_wikipedia_url(self, query: str) -> str:
        normalized = query.strip().replace(" ", "_")
        return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(normalized, safe='_')}"

    def _extract_first_paragraph_js(self) -> str:
        # Deterministic Wikipedia main-body extraction: skip hatnotes, navboxes, banners, tables, hidden UI.
        return r"""(async () => {
  const wikiHost = !!(location.hostname||'').match(/(^|\.)wikipedia\.org$/i);
  let root = wikiHost ? document.querySelector('#mw-content-text') : null;
  if (!root) {
    root = document.querySelector('main') || document.querySelector('article') || document.body;
  }
  if (!root) return '';

  const waitUntil = (pred, ms) => new Promise((res) => {
    const t0 = Date.now();
    (function tick() {
      try {
        if (pred()) return res(true);
      } catch (e) {}
      if (Date.now() - t0 > ms) return res(false);
      requestAnimationFrame(tick);
    })();
  });

  await waitUntil(() => !!(wikiHost ? document.querySelector('#mw-content-text p') && document.querySelector('#firstHeading') : root.querySelector('p')), wikiHost ? 20000 : 8000);

  const skipClosest = wikiHost ? (
    '.hatnote,.dablink,.rellink,.ambox,.sistersitebox,.navbox,.vertical-navbox,.navbox-inner,' +
    '.infobox,.sidebar,.portal,.thumbnail,.thumb,.thumbinner,#toc,.toc,.shortdescription,.mw-empty-elt'
  ) : 'style,script,noscript';

  const minWords = 25;
  const badPhrase = (t)=> /may refer\s*to:|disambiguation|cookie|temporary account|\bnewsletter\b|submit your|contest/i.test(t||'');

  const wordCount = (t) => ((t||'').trim().match(/\b[A-Za-z0-9'_-]+\b/g) || []).length;
  const isHidden = (el) => {
    try {
      let n = el;
      while (n && n!==document.body) {
        const st = window.getComputedStyle(n);
        if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0' || Number(st.fontSize.replace('px',''))===0)
          return true;
        n = n.parentElement;
      }
    } catch (e) {}
    return false;
  };

  let candidates = [...root.querySelectorAll('.mw-parser-output > p')];
  if (!candidates.length) {
    candidates = [...root.querySelectorAll('p')];
  }
  for (const p of candidates) {
    if (p.closest('table') || p.closest('figcaption')) continue;
    if (!p.closest || p.closest(skipClosest)) continue;
    if (p.closest('li')) continue;
    const t = (p.innerText || '').trim().replace(/\s+/g,' ');
    if (!t || t.length < 60) continue;
    if (isHidden(p)) continue;
    if (badPhrase(t)) continue;
    if (wordCount(t) < minWords) continue;
    return t;
  }
  return '';
})()"""

    def _looks_like_selector(self, text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return False
        return (len(t) < 80) and any(token in t for token in ["#", ".", ">", "[", "]", ":"])

    def _phase_for_state(self) -> str:
        mem = self._runtime_memory
        if mem["file_saved"]:
            return "COMPLETE"
        if mem["extracted_text"]:
            return "SAVE"
        if "search_executed" in mem["completed_goals"] or "wikipedia.org/wiki/" in (mem["current_url"] or ""):
            return "EXTRACT"
        if "navigate_to_target" in mem["completed_goals"]:
            return "SEARCH"
        return "NAVIGATE"

    def _update_runtime_memory_from_messages(self, messages: List[BaseMessage]):
        current_url = self._extract_url_from_messages(messages)
        self._runtime_memory["current_url"] = current_url
        self._runtime_memory["expected_query"] = self._extract_expected_query(messages)
        self._runtime_memory["expected_file"] = self._extract_expected_file(messages)
        extracted = self._extract_paragraph_text(messages)
        if extracted:
            self._runtime_memory["extracted_text"] = extracted
            self._runtime_memory["extracted_data_status"] = True
        if current_url:
            visited = self._runtime_memory["visited_urls"]
            visited[current_url] = visited.get(current_url, 0) + 1
        self._runtime_memory["phase"] = self._phase_for_state()

    def _compact_runtime_summary(self) -> str:
        completed = ",".join(self._runtime_memory["completed_goals"][-2:]) or "-"
        last_actions = ",".join(self._runtime_memory["last_actions"][-5:]) or "-"
        return (
            f"CURRENT_PAGE={self._runtime_memory['current_url'] or '-'}\n"
            f"LAST_ACTION={self._runtime_memory['last_actions'][-1] if self._runtime_memory['last_actions'] else '-'}\n"
            f"COMPLETED=[{completed}]\n"
            f"LAST5=[{last_actions}]\n"
            f"REPEATS={self._runtime_memory['repeated_actions']}\n"
            f"EXTRACTED={self._runtime_memory['extracted_data_status']}\n"
            f"FILE_SAVED={self._runtime_memory['file_saved']}\n"
            f"NEXT_EXPECTED={self._runtime_memory['expected_query'] or 'extract_first_paragraph'}\n"
            f"TARGET_FILE={self._runtime_memory['expected_file']}\n"
            f"PHASE={self._runtime_memory['phase']}"
        )

    def _apply_guardrails(self, dsl: SimpleActionDSL) -> SimpleActionDSL:
        mem = self._runtime_memory
        last_actions = mem["last_actions"]
        current_url = (mem["current_url"] or "").strip().lower()
        dsl_url = (dsl.url or "").strip().lower()
        phase = mem["phase"]

        # Selector-like extraction internals are forbidden from model output.
        if self._looks_like_selector(dsl.query or "") or self._looks_like_selector(dsl.content or ""):
            dsl.action = "EXTRACT_FIRST_PARAGRAPH"
            dsl.query = None
            dsl.content = None

        save_candidate = (dsl.content or mem.get("extracted_text") or "").strip()
        if dsl.action == "SAVE_MARKDOWN" and self._candidate_paragraph_ok(save_candidate):
            dsl.content = save_candidate
            return dsl

        if dsl.action == "DONE" and mem.get("file_saved"):
            return dsl

        # Deterministic phase progression: runtime owns workflow sequencing.
        if phase == "NAVIGATE":
            dsl.action = "OPEN_URL"
            dsl.url = "https://wikipedia.org"
        elif phase == "SEARCH":
            dsl.action = "SEARCH_WIKIPEDIA"
            dsl.query = mem["expected_query"] or "Artificial Intelligence"
        elif phase == "EXTRACT":
            dsl.action = "EXTRACT_FIRST_PARAGRAPH"
        elif phase == "SAVE":
            dsl.action = "SAVE_MARKDOWN"
            dsl.content = mem["extracted_text"]
        elif phase == "COMPLETE":
            dsl.action = "DONE"
            dsl.summary = dsl.summary or "Task completed with deterministic pipeline."
            dsl.success = True

        if dsl.action == "OPEN_URL" and dsl_url and dsl_url == current_url:
            visited = mem["visited_urls"].get(mem["current_url"], 0)
            if visited >= 1:
                logger.warning(f"[NAV_BLOCKED] Forbidding repeated navigation to same URL: {dsl.url}")
                dsl.action = "SEARCH_WIKIPEDIA"
                dsl.query = mem["expected_query"] or "Artificial Intelligence"
                dsl.url = None

        action_name = dsl.action
        if len(last_actions) >= 2 and last_actions[-1] == action_name and last_actions[-2] == action_name:
            same_url = (mem["last_url_for_action"] or "").strip().lower() == current_url
            if same_url:
                logger.warning(f"[FORCE_REPLAN] Repeated action '{action_name}' 3 times on unchanged URL.")
                if action_name in {"OPEN_URL", "WAIT_SHORT"}:
                    if not mem["extracted_data_status"]:
                        dsl.action = "EXTRACT_FIRST_PARAGRAPH"
                    elif not mem["file_saved"]:
                        dsl.action = "SAVE_MARKDOWN"
                        dsl.content = mem["extracted_text"]
                    else:
                        dsl.action = "DONE"
                        dsl.summary = "Stopping due to repeated non-progress actions."
                        dsl.success = False
                elif action_name == "SEARCH_WIKIPEDIA":
                    dsl.action = "DONE"
                    dsl.summary = "Stopping due to repeated search loop without progress."
                    dsl.success = False
                elif action_name == "EXTRACT_FIRST_PARAGRAPH":
                    if self._candidate_paragraph_ok(mem.get("extracted_text") or ""):
                        dsl.action = "SAVE_MARKDOWN"
                        dsl.content = mem["extracted_text"]
                    else:
                        dsl.action = "DONE"
                        dsl.summary = "Stopping: extraction repeated without usable paragraph."
                        dsl.success = False

        if dsl.action == "DONE" and mem["extracted_text"] and not mem["file_saved"]:
            dsl.action = "SAVE_MARKDOWN"
            dsl.content = mem["extracted_text"]
        return dsl

    def _track_progress(self, dsl: SimpleActionDSL):
        mem = self._runtime_memory
        action = dsl.action
        mem["last_actions"].append(action)
        mem["last_actions"] = mem["last_actions"][-5:]
        mem["repeated_actions"][action] = mem["repeated_actions"].get(action, 0) + 1
        mem["last_url_for_action"] = mem["current_url"]
        if action == "OPEN_URL":
            mem["completed_goals"].append("navigate_to_target")
        if action == "SEARCH_WIKIPEDIA":
            mem["completed_goals"].append("search_executed")
        if action == "EXTRACT_FIRST_PARAGRAPH":
            mem["extracted_data_status"] = True
            mem["completed_goals"].append("extract_first_paragraph")
        if action == "SAVE_MARKDOWN":
            mem["completed_goals"].append("save_markdown")
        mem["completed_goals"] = mem["completed_goals"][-4:]
        mem["phase"] = self._phase_for_state()

    def _translate_dsl_to_browser_action(self, dsl: SimpleActionDSL) -> Dict[str, Any]:
        if dsl.action == "OPEN_URL":
            return {"navigate": {"url": dsl.url}}
        if dsl.action == "SEARCH_WIKIPEDIA":
            query = dsl.query or self._runtime_memory["expected_query"] or "Artificial Intelligence"
            return {"navigate": {"url": self._search_wikipedia_url(query)}}
        if dsl.action == "EXTRACT_FIRST_PARAGRAPH":
            return {"evaluate": {"code": self._extract_first_paragraph_js()}}
        if dsl.action == "SAVE_MARKDOWN":
            content = (dsl.content or self._runtime_memory["extracted_text"] or "").strip()
            if self._looks_like_selector(content) or not self._candidate_paragraph_ok(content):
                return {"evaluate": {"code": self._extract_first_paragraph_js()}}
            self._runtime_memory["save_action_dispatched"] = True
            return {
                "write_markdown": {
                    "filename": self._runtime_memory["expected_file"].replace("./", ""),
                    "content": content,
                }
            }
        if dsl.action == "WAIT_SHORT":
            return {"wait": {"seconds": dsl.seconds or 1}}
        if dsl.action == "DONE":
            return {"done": {"text": dsl.summary, "success": bool(dsl.success if dsl.success is not None else True)}}
        raise ValueError(f"Unhandled DSL action: {dsl.action}")

    def _build_agent_output_json(self, translated_action: Dict[str, Any], dsl: SimpleActionDSL) -> str:
        next_goal = f"Execute {dsl.action}"
        if dsl.action == "DONE":
            next_goal = "Task completed"
        payload = {
            "thinking": f"Using DSL action {dsl.action}",
            "evaluation_previous_goal": "Continuing execution.",
            "memory": f"Last DSL action: {dsl.action}",
            "next_goal": next_goal,
            "plan_update": [],
            "action": [translated_action],
        }
        return json.dumps(payload)

    def _build_done_output_json(self, text: str, success: bool = False) -> str:
        payload = {
            "thinking": "Terminating cleanly after output/translation mismatch.",
            "evaluation_previous_goal": "Unable to execute a valid non-done action in current tool context.",
            "memory": "Fallback to done action",
            "next_goal": "Terminate run",
            "plan_update": [],
            "action": [{"done": {"text": text, "success": success}}],
        }
        return json.dumps(payload)

    def _log_dsl_event(self, inference_num: int, stage: str, data: Any):
        logger.info(f"[{stage}] {data}")
        file_path = f"logs/dsl_outputs/dsl_{int(time.time() * 1000)}_{inference_num}.json"
        with open(file_path, "w") as f:
            json.dump({"stage": stage, "inference_number": inference_num, "data": data}, f, indent=2)

    async def _request_dsl_correction(self, malformed_content: str, error: str) -> str:
        correction_system = (
            "You are a strict JSON repair assistant.\n"
            "Return ONLY valid JSON.\n"
            "No markdown. No explanations. No extra text.\n"
            "Use ONLY this schema: "
            '{"action":"OPEN_URL|SEARCH_WIKIPEDIA|EXTRACT_FIRST_PARAGRAPH|SAVE_MARKDOWN|WAIT_SHORT|DONE",'
            '"url":"","query":"","content":"","seconds":1,"summary":"","success":true}'
        )
        correction_prompt = (
            "Fix this model output into a valid action DSL JSON object.\n"
            f"Validation error: {error}\n"
            f"Malformed output:\n{malformed_content[:1500]}"
        )
        response = await self._client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "system": correction_system,
                "prompt": correction_prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0},
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")

    async def ainvoke(
        self, messages: List[BaseMessage], output_format: Optional[Type[T]] = None, **kwargs: Any
    ) -> Union[ChatInvokeCompletion[T], ChatInvokeCompletion[str]]:
        self._inference_count += 1
        inference_num = self._inference_count

        logger.info(f"[CHECKPOINT] Ollama inference started")

        ollama_messages = []
        compact_messages = messages[-3:] if len(messages) > 3 else messages
        self._update_runtime_memory_from_messages(compact_messages)

        if output_format and getattr(output_format, "__name__", "") == "AgentOutput":
            forced = self._try_deterministic_agent_step(output_format, inference_num)
            if forced is not None:
                return forced

        ollama_messages.append({"role": "system", "content": "RUNTIME_STATE\n" + self._compact_runtime_summary()})
        for msg in compact_messages:
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', '')

            if isinstance(content, list):
                processed_parts = []
                for part in content:
                    if isinstance(part, dict):
                        # Reduce prompt size: strip long texts if they seem like noise
                        text = part.get('text', str(part))
                        if len(text) > 800:
                            text = text[:800] + "... (truncated)"
                        processed_parts.append(text)
                    elif hasattr(part, 'text'):
                        text = part.text
                        if len(text) > 800:
                            text = text[:800] + "... (truncated)"
                        processed_parts.append(text)
                    else:
                        processed_parts.append(str(part))
                content = "\n".join(processed_parts)
            elif isinstance(content, str):
                if len(content) > 1200:
                    content = content[:1200] + "... (truncated for local model)"
            else:
                content = str(content)

            ollama_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        payload["format"] = "json"

        start_time = time.time()
        raw_response = None
        data = None

        try:
            logger.info(f"[CHECKPOINT] Sending prompt to Ollama (timeout: {INFERENCE_TIMEOUT}s)")
            response = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            raw_response = data.get("message", {}).get("content", "")

            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            logger.info(f"[CHECKPOINT] Ollama inference completed. Latency: {latency_ms:.2f}ms")

            os.makedirs("logs", exist_ok=True)
            log_file = f"logs/ollama_raw_{int(time.time() * 1000)}.json"
            log_data = {
                "inference_number": inference_num,
                "payload_truncated": {k: (v[:1000] + "..." if isinstance(v, str) and len(v) > 1000 else v) for k, v in [("messages", ollama_messages)]},
                "raw_response": raw_response,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "response_hash": hash(raw_response) if raw_response else None
            }
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)

            current_hash = hash(raw_response)
            if self._last_response_hash == current_hash:
                logger.warning(f"[LOOP_DETECTION] Same response hash repeated: {current_hash}")
            self._last_response_hash = current_hash

            logger.info(f"[CHECKPOINT] Parsing response")

            completion: Union[T, str]
            parse_success = False

            if output_format:
                output_name = getattr(output_format, "__name__", "")
                if output_name != "AgentOutput":
                    completion = output_format.model_validate_json(raw_response)
                    return ChatInvokeCompletion(
                        completion=completion,
                        usage=ChatInvokeUsage(
                            prompt_tokens=prompt_tokens,
                            prompt_cached_tokens=0,
                            prompt_cache_creation_tokens=0,
                            prompt_image_tokens=0,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens
                        ),
                        stop_reason="stop"
                    )

                parsed_json = None
                dsl = None
                last_error = None
                for _ in range(3):
                    try:
                        parsed_json = self._extract_json_object(raw_response)
                        self._coerce_action_payload(parsed_json)
                        dsl = self._validate_dsl(parsed_json)
                        break
                    except (ValueError, ValidationError, json.JSONDecodeError) as e:
                        self._dsl_parse_failures += 1
                        last_error = str(e)
                        logger.error(f"[PARSE_ERROR] DSL parsing failed: {e}")
                        raw_response = await self._request_dsl_correction(raw_response, str(e))

                if not dsl:
                    raise Exception(f"Failed to parse DSL after 3 attempts: {last_error}")

                self._runtime_memory["phase"] = self._phase_for_state()
                dsl = self._apply_guardrails(dsl)
                translated_action = self._translate_dsl_to_browser_action(dsl)
                self._track_progress(dsl)
                self._log_dsl_event(inference_num, "DSL_OUTPUT", parsed_json)
                self._log_dsl_event(inference_num, "TRANSLATED_ACTION", translated_action)
                agent_output_json = self._build_agent_output_json(translated_action, dsl)
                try:
                    completion = output_format.model_validate_json(agent_output_json)
                except Exception:
                    done_json = self._build_done_output_json(
                        "Terminating: translated action not allowed in current step context.",
                        success=False,
                    )
                    completion = output_format.model_validate_json(done_json)
                parse_success = True
                logger.info(f"[EXECUTION_RESULT] Action ready for browser-use")
            else:
                completion = raw_response
                parse_success = True

            return ChatInvokeCompletion(
                completion=completion,
                usage=ChatInvokeUsage(
                    prompt_tokens=prompt_tokens,
                    prompt_cached_tokens=0,
                    prompt_cache_creation_tokens=0,
                    prompt_image_tokens=0,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                ),
                stop_reason="stop"
            )

        except httpx.TimeoutException:
            logger.error(f"[TIMEOUT] Inference #{inference_num} timed out after {INFERENCE_TIMEOUT}s")
            if self._inference_count >= 3:
                logger.error(f"[LOOP_DETECTION] Hit 3 inference limit, terminating")
                raise Exception(f"Timeout limit reached after 3 retries")
            raise
        except Exception as e:
            logger.error(f"Ollama ainvoke #{inference_num} failed: {e}")
            if raw_response:
                logger.error(f"[RAW_RESPONSE_DUMP] {raw_response[:1000]}")
            raise

    async def close(self):
        await self._client.aclose()

def get_chat_model():
    """Returns the custom OllamaLLM that follows the browser-use protocol."""
    return OllamaLLM()
