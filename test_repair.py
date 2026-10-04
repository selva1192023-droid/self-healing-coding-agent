
from repair.self_healing_agent import SelfHealingAgent


def main():
    # Initialize the self-healing agent
    agent = SelfHealingAgent()

    # Corrected code for the broken Python file
    fixed = """def greet():
    print("Hello from self-healing agent")

greet()
"""

    # Repair and verify with explicit confirmation
    result = agent.repair_and_verify(
        "repair_test.py",
        fixed,
        confirm=True
    )

    # Display the result
    print("\n=== SELF-HEALING AGENT RESULT ===")
    print(result)


if __name__ == "__main__":
    main()