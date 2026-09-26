import pytest
from executor.vector_memory import (
    store_vector_memory,
    search_vector_memory,
    generate_embedding,
    get_vector_stats
)
from executor.react_agent import run_react_task, GLOBAL_TOOL_REGISTRY
from executor.swarm_orchestrator import run_swarm

def test_vector_memory():
    doc1 = "Python backend architecture with microservices and API endpoints."
    doc2 = "Greek salad with feta cheese and olive oil recipe."
    
    id1 = store_vector_memory(doc1, {"category": "tech"})
    id2 = store_vector_memory(doc2, {"category": "cooking"})
    
    assert id1 > 0
    assert id2 > 0
    
    results = search_vector_memory("microservices backend python", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == id1
    assert results[0]["metadata"]["category"] == "tech"
    
    stats = get_vector_stats()
    assert stats["total_vectors"] >= 2

def test_react_agent():
    tools = GLOBAL_TOOL_REGISTRY.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "bash" in tool_names
    assert "read_file" in tool_names
    assert "git_status" in tool_names

    res = run_react_task("Check git status and summarize")
    assert res["status"] == "completed"
    assert len(res["steps"]) > 0
    assert "reflection" in res

def test_swarm_orchestrator():
    res = run_swarm("Refactor router and run test suite")
    assert res["status"] == "completed"
    assert res["agent_count"] == 4
    roles = [step["role"] for step in res["trace"]]
    assert "architect" in roles
    assert "coder" in roles
    assert "reviewer" in roles
