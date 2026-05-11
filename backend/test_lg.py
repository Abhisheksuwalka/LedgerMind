import asyncio
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import Annotated
import operator

class State(TypedDict):
    completed: Annotated[list[str], operator.add]

def a(state): return {"completed": ["a"]}
def b(state): return {"completed": ["b"]}
def c(state): return {"completed": ["c"]}

def route(state):
    print(f"DEBUG route: state={state}")
    if set(["b", "c"]).issubset(state.get("completed", [])):
        return "d"
    return END

graph = StateGraph(State)
graph.add_node("a", a)
graph.add_node("b", b)
graph.add_node("c", c)
graph.add_node("d", lambda s: {"completed": ["d"]})

graph.set_entry_point("a")
graph.add_edge("a", "b")
graph.add_edge("a", "c")
graph.add_conditional_edges("b", route)
graph.add_conditional_edges("c", route)
graph.add_edge("d", END)

app = graph.compile()

async def main():
    result = await app.ainvoke({"completed": []})
    print(f"FINAL STATE: {result}")

asyncio.run(main())
