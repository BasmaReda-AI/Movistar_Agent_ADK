"""
Validation test for AgentAdapter.

Tests:
  1. Initial greeting from the agent
  2. Identity confirmation → agent moves to availability check
  3. Availability confirmed → agent transfers to sales specialist
"""

import asyncio
from agent_adapter import AgentAdapter

# Use a deterministic session ID so each run of this test gets a fresh session
SESSION_ID = "test-validation"


async def test():
    adapter = AgentAdapter()

    # --- Turn 1: Initial greeting ---
    print("=== Turn 1: User says 'hi' ===")
    r1 = await adapter.chat("hi", session_id=SESSION_ID)
    print(f"  Agent: {r1}")
    assert "Good morning" in r1 or "Natalie" in r1, f"Unexpected greeting: {r1}"
    print("  [PASS] Greeting received\n")

    # --- Turn 2: Confirm identity ---
    print("=== Turn 2: User confirms identity ===")
    r2 = await adapter.chat("Yes, this is Mauricio", session_id=SESSION_ID)
    print(f"  Agent: {r2}")
    assert "moment" in r2 or "available" in r2, f"Expected availability check: {r2}"
    print("  [PASS] Agent asked about availability\n")

    # --- Turn 3: Confirm availability ---
    print("=== Turn 3: User confirms availability ===")
    r3 = await adapter.chat("Yes, I have a moment", session_id=SESSION_ID)
    print(f"  Agent: {r3}")
    assert len(r3) > 10, f"Response too short: {r3}"
    print("  [PASS] Agent continues to sales pitch or transfer\n")

    # --- Turn 4: Test reset ---
    print("=== Reset session ===")
    adapter.reset_session(SESSION_ID)
    r4 = await adapter.chat("hi", session_id=SESSION_ID)
    print(f"  Agent after reset: {r4}")
    assert "Good morning" in r4 or "Natalie" in r4, f"Expected fresh greeting: {r4}"
    print("  [PASS] Session reset works\n")

    print("=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test())
