def logging_history(content):
    with open("./history.txt", "a", encoding="utf-8") as f:
        f.write(f"{content}")

def pretty_event_print(ev):
    content = ""
    if "steps" in ev:
        for s in ev["steps"]:
            print("[STEP LOG] " + str(s.action.log))
            content = "[STEP LOG] " + str(s.action.log) + "\n"

            if getattr(s, "observation", None) is not None:
                print("[OBSERVATION]\n" + str(s.observation))
                content += "[OBSERVATION]\n" + str(s.observation)
    elif "actions" in ev:
        for a in ev["actions"]:
            print(f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}")
            content += f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}"
    elif "messages" in ev:
        for m in ev["messages"]:
            print(f"\nAnswer > {m.content.split("Final Answer: ")[-1]}")
            content += f"Answer > {m.content.split("Final Answer: ")[-1]}\n{'===' * 30}\n"

    logging_history(f"{content}\n\n")