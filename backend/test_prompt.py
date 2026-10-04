from app.api.coding import build_agent_prompt

context = {
    "project_scan": {
        "files": [
            "agents/planner.py",
            "agents/agent_runner.py",
            "app/api/coding.py",
            "app/services/llm_service.py",
            "code_engine/context_manager.py",
            "execution/code_executor.py",
            "repair/repair_engine.py",
            "repair/self_healing_agent.py",
            "testing/error_detector.py",
            "tools/tool_executor.py"
        ]
    },
    "target_file": "workspace/hello.py",
    "file_content": "print('Hello from self-healing agent')",
    "code_structure": None
}

plan = {
    "status": "success",
    "task_type": "explain",
    "total_steps": 5,
    "execution_started": False,
    "files_modified": []
}

p = build_agent_prompt(
    "Explain what this project does",
    context,
    plan
)

print("\n========== GENERATED PROMPT ==========\n")
print(p)

print("\n========== PROMPT VALIDATION ==========\n")

print("UNTRUSTED DATA:", "untrusted data" in p.lower())
print("NO INVENTED MODULES:", "Do not invent modules" in p)
print("PROJECT EXPLANATION:", "explain the existing project" in p.lower())

print("\n========== TEST COMPLETE ==========")