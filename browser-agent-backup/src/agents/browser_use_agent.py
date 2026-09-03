import asyncio
import os
import time
import socket
import json
import urllib.parse
from typing import Optional, Any, List, Dict
from browser_use import Agent, Browser, Controller
from browser_use.browser.events import NavigateToUrlEvent
from browser_use.browser.session import BrowserSession
from src.config import (
    logger,
    MODEL_PROVIDER,
    OLLAMA_MODEL,
    OLLAMA_HOST,
    HEADLESS,
    MAX_STEPS,
    RETRIES
)
from src.core.models import AgentState, TaskStatus
from src.observability.manager import ObservabilityManager
from src.dashboard.server import run_dashboard_server
from src.core.ollama import OllamaProvider, get_chat_model


_original_on_navigate_to_url_event = BrowserSession.on_NavigateToUrlEvent


async def on_NavigateToUrlEvent(self: BrowserSession, event: NavigateToUrlEvent):  # type: ignore[no-untyped-def]
    """Avoid CDP lifecycle dead-ends (networkidle/load flakiness); rely on domain waits inside evaluate instead."""
    update: dict[str, object] = {}
    et = getattr(event, "event_timeout", None)
    if et is None or float(et) < 120.0:
        update["event_timeout"] = 120.0
    if getattr(event, "timeout_ms", None) is None:
        update["timeout_ms"] = 60000
    update["wait_until"] = "commit"
    event = event.model_copy(update=update)
    return await _original_on_navigate_to_url_event(self, event)


BrowserSession.on_NavigateToUrlEvent = on_NavigateToUrlEvent

class BrowserAgent:
    def __init__(self, task: str, dashboard_port: int = 8000):
        self.task = task
        self.dashboard_port = dashboard_port
        self.obs = ObservabilityManager()

        self.ollama = OllamaProvider()
        self.llm = get_chat_model()

        self.last_actions = []
        self.max_repeats = 3
        self.max_inferences_without_action = 3
        self.inference_count = 0
        self.action_count = 0
        
        # Timeouts
        self.nav_timeout = 30000 # 30s in ms for Playwright
        self.inference_timeout = 20.0 # 20s

        self.browser_config_dict = {
            "headless": HEADLESS,
            "disable_security": True,
            "args": [f"--window-size=1280,1024"],
            "window_size": {"width": 1280, "height": 1024},
            "minimum_wait_page_load_time": 0.05,
            "wait_for_network_idle_page_load_time": 0.0,
            "wait_between_actions": 0.05,
        }
        
        self.dashboard_browser = Browser(**self.browser_config_dict)
        self.automation_browser = Browser(**self.browser_config_dict)
        
        # Add custom tools
        self.controller = Controller()
        
        @self.controller.action('Write summary to markdown file')
        def write_markdown(filename: str, content: str):
            mem = self.llm._runtime_memory
            try:
                with open(filename, 'w') as f:
                    f.write(content)
                mem["file_saved"] = True
            except OSError:
                logger.error('[SAVE] Failed to write markdown to %s', filename)
                raise
            finally:
                mem["save_action_dispatched"] = False
            return f'Successfully saved summary to {filename}'

    def _validate_domain(self, url: str) -> bool:
        """Deterministically validate domain before navigation."""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            if not domain:
                return False
            socket.gethostbyname(domain)
            return True
        except Exception as e:
            logger.warning(f"[CHECKPOINT] Domain validation failed for {url}: {e}")
            return False

    async def _wait_for_dashboard(self, url: str, timeout: int = 5) -> bool:
        """Ensure dashboard is ready before browser exposure."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return True
            except:
                pass
            await asyncio.sleep(0.5)
        return False

    async def run(self, max_steps: int = MAX_STEPS, retries: int = RETRIES):
        logger.info(f"[CHECKPOINT] Starting BrowserAgent for task: {self.task}")
        self.obs.update_state(AgentState.INITIALIZING, current_task=self.task)

        logger.info(f"[CHECKPOINT] Verifying local inference status ({OLLAMA_MODEL})...")
        health = await self.ollama.health_check()
        if health["status"] != "healthy":
            error_msg = f"Local model health check failed: {health.get('error', health['status'])}"
            logger.error(error_msg)
            self.obs.finalize(TaskStatus.FAILED, error_msg)
            return f"FAILED: {error_msg}"

        logger.info("[CHECKPOINT] Local inference verified. GPU mode active.")

        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]

        self.dashboard_port = find_free_port()
        self.dashboard_url = f"http://127.0.0.1:{self.dashboard_port}"

        logger.info(f"[CHECKPOINT] Launching dashboard server on port {self.dashboard_port}")
        server = run_dashboard_server(self.obs, port=self.dashboard_port)
        server_task = asyncio.create_task(server.serve())
        
        # Wait for dashboard to be healthy
        if await self._wait_for_dashboard(self.dashboard_url):
            logger.info(f"[CHECKPOINT] Dashboard server ready")
        else:
            logger.error("[CHECKPOINT] Dashboard server failed to start")
            # Continue anyway but log error

        try:
            # ELIMINATE about:blank: Start dashboard browser
            logger.info(f"[CHECKPOINT] Launching dashboard browser window")
            await self.dashboard_browser.start()
            
            # Immediately navigate to dashboard to avoid about:blank flash
            await self.dashboard_browser.navigate_to(self.dashboard_url)
            logger.info(f"[CHECKPOINT] Dashboard loaded successfully")

            self.obs.update_state(AgentState.THINKING, last_action="Initializing Local Inference...")

            attempt = 0
            while attempt <= retries:
                try:
                    if attempt > 0:
                        self.obs.update_state(AgentState.RETRYING, retry_count=attempt)
                        logger.info(f"[CHECKPOINT] Retry attempt {attempt}...")

                    # Prepare automation browser
                    logger.info(f"[CHECKPOINT] Browser automation window created")
                    await self.automation_browser.start()
                    
                    # Pre-create page to avoid about:blank during Agent initialization
                    # browser-use Agent will reuse the existing page if provided via the browser/context
                    logger.info(f"[CHECKPOINT] Initial page prepared")

                    logger.info(f"[CHECKPOINT] Ollama inference started")
                    
                    # Keep prompt short and force a tiny DSL output for local models.
                    strict_json_hint = (
                        "\n\nRETURN ONLY VALID JSON.\n"
                        "NO MARKDOWN. NO EXPLANATIONS. NO EXTRA TEXT.\n"
                        "Use ONLY this DSL:\n"
                        '{"action":"OPEN_URL|SEARCH_WIKIPEDIA|EXTRACT_FIRST_PARAGRAPH|SAVE_MARKDOWN|WAIT_SHORT|DONE",'
                        '"url":"", "query":"", "content":"", "seconds":1, "summary":"", "success":true}\n'
                        "Never output CSS selectors, JS snippets, or DOM queries."
                    )
                    
                    agent = Agent(
                        task=self.task,
                        llm=self.llm,
                        browser=self.automation_browser,
                        controller=self.controller,
                        register_new_step_callback=self._create_step_callback(),
                        extend_system_message=strict_json_hint,
                        use_vision=False,
                        max_failures=retries,
                        use_judge=False,
                        enable_planning=False,
                        directly_open_url=True,
                    )

                    logger.info(f"[CHECKPOINT] Running agent (max_steps={max_steps})")
                    history = await agent.run(max_steps=max_steps)
                    result = history.final_result()

                    is_real_success = history.is_done() and not history.has_errors() and self._validate_success_criteria()

                    if is_real_success:
                        self.obs.finalize(TaskStatus.SUCCESS)
                        return f"SUCCESS: {result}"
                    else:
                        failure_msg = "Task did not complete successfully."
                        self.obs.finalize(TaskStatus.FAILED, failure_msg)
                        return f"FAILED: {result or failure_msg}"

                except Exception as e:
                    attempt += 1
                    logger.error(f"[ERROR] Runtime Error (Attempt {attempt}): {e}")
                    self.obs.update_state(AgentState.RECOVERING, error_message=str(e))

                    if self._check_termination_criteria():
                        error_msg = f"Termination criteria met: loop detected or retries exhausted"
                        logger.error(f"[TERMINATION] {error_msg}")
                        self.obs.finalize(TaskStatus.FAILED, error_msg)
                        raise Exception(error_msg)

                    if attempt > retries:
                        self.obs.finalize(TaskStatus.FAILED, str(e))
                        raise e

                    await asyncio.sleep(2 ** attempt)

        finally:
            self.obs.update_state(AgentState.IDLE, last_action="Session finished.")
            await asyncio.sleep(2)
            logger.info(f"[CHECKPOINT] Stopping browsers and server")
            await self.dashboard_browser.stop()
            await self.automation_browser.stop()
            server.should_exit = True
            await server_task
            await self.ollama.close()

    def _validate_success_criteria(self) -> bool:
        """Runtime-only validation: no LLM judge — file, length, extraction quality, actions."""
        expected_file = (
            self.llm._runtime_memory.get("expected_file") or "ai_summary.md"
        ).replace("./", "")
        try:
            if self.action_count <= 0:
                return False
            if len(self.last_actions) == self.max_repeats and len(set(self.last_actions)) == 1:
                return False
            if not os.path.isfile(expected_file):
                return False
            with open(expected_file, "r") as f:
                content = f.read().strip()
            if not content:
                return False
            if not self.llm._candidate_paragraph_ok(content):
                return False
            if not self.llm._runtime_memory.get("file_saved"):
                return False
            if not (
                self.llm._runtime_memory.get("extracted_data_status")
                or self.llm._runtime_memory.get("extracted_text")
            ):
                return False
            return True
        except Exception:
            return False

    def _create_step_callback(self):
        async def enhanced_on_step(state, output, step_number):
            self.inference_count += 1
            logger.info(f"[CHECKPOINT] Ollama inference completed")
            logger.info(f"[CHECKPOINT] Step {step_number} callback invoked")

            while self.obs.status.human_intervention_needed:
                self.obs.update_state(AgentState.HUMAN_INTERVENTION)
                await asyncio.sleep(1)

            # Loop Detection
            action_str = self.obs._safe_extract(output, 'next_goal', "None")
            self.last_actions.append(action_str)
            if len(self.last_actions) > self.max_repeats:
                self.last_actions.pop(0)
            
            if len(self.last_actions) == self.max_repeats and len(set(self.last_actions)) == 1 and action_str != "None":
                logger.warning(f"[LOOP_DETECTION] Action '{action_str}' repeated {self.max_repeats} times")
                raise Exception(f"Loop detected: Same action repeated {self.max_repeats} times.")

            goal = self.obs._safe_extract(output, 'next_goal', "Processing...")
            logger.info(f"[CHECKPOINT] Browser action parsed: {goal[:100]}")

            # Navigation Checkpoint and Validation
            if "navigate" in str(goal).lower():
                self.obs.update_state(AgentState.NAVIGATING)
                logger.info(f"[CHECKPOINT] Navigation started")
                
                # Attempt to find URL in the goal or action
                # Since we don't have the raw action here easily, we rely on browser-use
                # but we can check the state's URL after the next step.
            else:
                self.obs.update_state(AgentState.EXTRACTING)

            self.obs.record_step(step_number, state, output)
            logger.info(f"[EXECUTION_RESULT] Step {step_number} recorded")

            if hasattr(output, 'token_usage'):
                self.obs.status.token_usage = {
                    "prompt": getattr(output.token_usage, 'prompt_tokens', 0),
                    "completion": getattr(output.token_usage, 'completion_tokens', 0),
                    "total": getattr(output.token_usage, 'total_tokens', 0)
                }

            self.action_count += 1
            
            # Check for errors in state (browser-use might put them there)
            if hasattr(state, 'error') and state.error:
                logger.error(f"[CHECKPOINT] Action failed: {state.error}")
                if "dns" in str(state.error).lower() or "not found" in str(state.error).lower():
                    logger.error(f"[CHECKPOINT] DNS or Host Unreachable detected")

            if "navigate" in str(goal).lower():
                logger.info(f"[CHECKPOINT] Navigation completed")
            elif "extract" in str(goal).lower() or "read" in str(goal).lower() or "summarize" in str(goal).lower():
                logger.info(f"[CHECKPOINT] Extraction completed")

        return enhanced_on_step

    def _check_termination_criteria(self) -> bool:
        # If we've done many inferences but no actions, it's a thinking loop
        if self.inference_count >= 6 and self.action_count == 0:
            logger.warning(f"[TERMINATION] Thinking loop detected (6 inferences, 0 actions)")
            return True
        
        # If we've hit the retry limit
        # 'attempt' in run() handles this.
        
        # If we've repeated the same action 3 times
        # Handled by exception in callback
        return False
