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

graph = StateGraph(State)
graph.add_node("a", a)
graph.add_node("b", b)
graph.add_node("c", c)
graph.add_node("d", lambda s: {"completed": ["d"]})

graph.set_entry_point("a")
graph.add_edge("a", "b")
graph.add_edge("a", "c")
graph.add_edge(["b", "c"], "d")
graph.add_edge("d", END)

app = graph.compile()

async def main():
    result = await app.ainvoke({"completed": []})
    print(f"FINAL STATE: {result}")

asyncio.run(main())
