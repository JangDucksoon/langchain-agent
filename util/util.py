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
                print("[OBSERVATION]\n" + str(s.observation) + "\n")
                content += "[OBSERVATION]\n" + str(s.observation) + "\n"
    elif "actions" in ev:
        for a in ev["actions"]:
            print(f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}")
            content += f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}"
    elif "messages" in ev:
        for m in ev["messages"]:
            print(f"\nAnswer > {m.content.split("Final Answer: ")[-1]}")
            content += f"Answer > {m.content.split("Final Answer: ")[-1]}\n{'===' * 30}\n"

    logging_history(f"{content}\n\n")

def pretty_event_print_api(ev):
    content = ""
    if "steps" in ev:
        for s in ev["steps"]:
            message = "[STEP LOG] " + str(s.action.log)
            yield message
            content = "[STEP LOG] " + str(s.action.log) + "\n"

            if getattr(s, "observation", None) is not None:
                message = "[OBSERVATION]\n" + str(s.observation) + "\n"
                yield message
                content += "[OBSERVATION]\n" + str(s.observation) + "\n"
    elif "actions" in ev:
        for a in ev["actions"]:
            message = f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}"
            yield message
            content += f"\n[ACTION] tool={a.tool}\n[ACTION INPUT] {a.tool_input}"
    elif "messages" in ev:
        for m in ev["messages"]:
            message = f"\n{m.content.split("Final Answer: ")[-1]}"
            yield message
            content += f"Answer > {m.content.split("Final Answer: ")[-1]}\n{'===' * 30}\n"

    logging_history(f"{content}\n\n")