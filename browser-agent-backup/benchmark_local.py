import asyncio
import time
import json
import psutil
import httpx
from src.config import OLLAMA_HOST, OLLAMA_MODEL

async def benchmark_ollama():
    print(f"🚀 Starting Local Inference Benchmark ({OLLAMA_MODEL})")
    print("--------------------------------------------------")
    
    results = {
        "model": OLLAMA_MODEL,
        "host": OLLAMA_HOST,
        "tests": []
    }
    
    prompts = [
        "What is the capital of France?",
        "Write a short python function to sort a list of numbers.",
        "Summarize the benefits of local AI inference."
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, prompt in enumerate(prompts):
            print(f"Test {i+1}/{len(prompts)}: '{prompt[:30]}...'")
            
            start_time = time.time()
            try:
                response = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                data = response.json()
                end_time = time.time()
                
                duration = end_time - start_time
                tokens = data.get("eval_count", 0)
                tps = tokens / duration if duration > 0 else 0
                
                test_result = {
                    "prompt": prompt,
                    "duration_sec": round(duration, 2),
                    "tokens": tokens,
                    "tokens_per_sec": round(tps, 2),
                    "status": "success"
                }
                results["tests"].append(test_result)
                print(f"   ✅ Done: {duration:.2f}s | {tps:.2f} tokens/sec")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["tests"].append({"prompt": prompt, "status": "failed", "error": str(e)})

    # Summary
    success_tests = [t for t in results["tests"] if t["status"] == "success"]
    if success_tests:
        avg_tps = sum(t["tokens_per_sec"] for t in success_tests) / len(success_tests)
        results["avg_tokens_per_sec"] = round(avg_tps, 2)
        print("\n--------------------------------------------------")
        print(f"📊 Benchmark Summary:")
        print(f"   Avg Tokens/Sec: {avg_tps:.2f}")
        print(f"   Tests Passed: {len(success_tests)}/{len(prompts)}")
    
    # Save report
    report_path = "benchmark_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(benchmark_ollama())
