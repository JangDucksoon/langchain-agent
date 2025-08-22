def pretty_event_print(ev):
    if "steps" in ev:
        for s in ev["steps"]:
            print("\n[STEP LOG]\n" + str(s.action.log))
            if getattr(s, "observation", None) is not None:
                print("[OBSERVATION]\n" + str(s.observation))
    elif "actions" in ev:
        for a in ev["actions"]:
            print(f"\n[ACTION] tool={a.tool}\n[ACTION INPUT]\n{a.tool_input}")
    elif "messages" in ev:
        for m in ev["messages"]:
            print(f"\nAnswer > {m.content.split("Final Answer: ")[-1]}")