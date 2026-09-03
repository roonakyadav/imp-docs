import asyncio
import sys
import os
from src.config import logger, validate_config, MAX_STEPS, RETRIES, DASHBOARD_PORT
from src.agents import BrowserAgent

async def run_task(task_description: str):
    """
    Executes a professional observable browser automation task.
    """
    if not validate_config():
        print("\n❌ Configuration Error: Please check your .env file.")
        print("Ensure OLLAMA_HOST and OLLAMA_MODEL are set correctly.")
        return

    print(f"\n🚀 Launching Local Observable Agent Runtime")
    print(f"🧠 Inference Provider: Ollama")
    print("--------------------------------------------------")

    try:
        # Initialize the professional agent
        agent = BrowserAgent(task=task_description, dashboard_port=DASHBOARD_PORT)
        
        # Run the agent with observability and dashboard
        result = await agent.run(max_steps=MAX_STEPS, retries=RETRIES)
        
        print("\n" + "="*50)
        print("✅ RUNTIME SESSION CONCLUDED")
        print("="*50)
        print(f"\n{result}")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Runtime Failure: {str(e)}")
        logger.error(f"Failed to execute task: {e}")

if __name__ == "__main__":
    # Use the specific validation task as default
    default_task = (
        "Open wikipedia.org, search for Artificial Intelligence, extract the first article paragraph, "
        "and save it into ai_summary.md"
    )
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("\n🤖 Welcome to the Professional Agent Runtime")
        print(f"Default Task: {default_task}")
        task_input = input("Enter task description (press Enter for default) > ").strip()
        task = task_input if task_input else default_task
    
    if task:
        try:
            asyncio.run(run_task(task))
        except KeyboardInterrupt:
            print("\n\n👋 Runtime interrupted. Closing safely...")
    else:
        print("No task provided. Exiting.")
