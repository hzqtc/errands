#!/usr/bin/env python3

from collections import defaultdict
from model import Model
from prompt import get_next_run_items
from typing import List
import re
import readline
import shlex
import sys


def parse_bool(val: str) -> bool:
  if val.lower() in ("true", "yes", "1"):
    return True
  if val.lower() in ("false", "no", "0"):
    return False
  raise ValueError(f"Invalid boolean: {val}")


def parse_list(val: str) -> List:
  return [item.strip() for item in val.split(",")]


def check_condition(condition, message):
  if not condition:
    raise ValueError(message)


def print_help():
  print("Commands:")
  print("  add store <name> <preferred: true|false>")
  print("  delete store <name>")
  print("  edit store <name> <preferred: true|false>")
  print("  add item <name> <[stores]> <interval_weeks>")
  print("  delete item <name>")
  print("  edit item <name> <[stores]> <interval_weeks>")
  print("  edit item")
  print("  list stores")
  print("  list items")
  print("  log_purcahse <item1> <item2>")
  print("  next_run")
  print("  help")
  print("  exit")


def execute_command(model: Model, line: str):
  args = shlex.split(line.strip())
  if not args:
    return

  cmd = args[0]

  if cmd == "help":
    print_help()

  elif cmd == "exit":
    raise EOFError()

  elif cmd == "add":
    check_condition(len(args) >= 2, "Usage: add [store|item]")
    if args[1] == "store":
      check_condition(len(args) >= 3, "Usage: add store <name> (<optional>)")
      name = args[2]
      preferred = parse_bool(args[3]) if len(args) > 3 else False
      model.add_store(name, preferred)
    elif args[1] == "item":
      check_condition(
        len(args) == 5, "Usage: add item <name> <store1,store2,...> <interval>"
      )
      name = args[2]
      stores = parse_list(args[3])
      interval = int(args[4])
      model.add_item(name, stores, interval)
    else:
      raise ValueError("Usage: add [store|item]")

  elif cmd == "delete":
    check_condition(len(args) >= 2, "Usage: delete [store|item]")
    if args[1] == "store":
      check_condition(len(args) == 3, "Usage: delete store <name>")
      model.delete_store(args[2])
    elif args[1] == "item":
      check_condition(len(args) == 3, "Usage: delete item <name>")
      model.delete_item(args[2])
    else:
      raise ValueError("Usage: delete [store|item]")

  elif cmd == "edit":
    check_condition(len(args) >= 2, "Usage: edit [store|item]")
    if args[1] == "store":
      check_condition(
        len(args) == 4,
        "Usage: edit store <name> [true|false] (whether store is preferred)",
      )
      name = args[2]
      preferred = parse_bool(args[3])
      model.edit_store(name, preferred)
    elif args[1] == "item":
      check_condition(
        len(args) >= 3,
        "Usage: edit item <name> or edit item <name> <store1,store2,...> <interval>",
      )
      name = args[2]
      if len(args) == 5:
        stores = parse_list(args[3])
        model.update_item_stores(name, stores)
        interval = int(args[4])
        model.update_item_interval(name, interval)
      else:
        run_item_edit_prompt(model, name)
    else:
      raise ValueError("Usage: edit [store|item]")

  elif cmd == "list":
    check_condition(len(args) == 2, "Usage: list stores|items")
    if args[1] == "stores":
      if not model.stores:
        print("No stores.")
      for s in model.stores:
        mark = "*" if s.preferred else " "
        print(f"{mark} {s.name}")
    elif args[1] == "items":
      if not model.items:
        print("No items.")
      for i in model.items:
        print(
          f"- {i.name}: every {i.interval_weeks} weeks at {i.stores}, last purchased on {i.purchased[-1] if i.purchased else None}"
        )
    else:
      raise ValueError("Usage: list stores|items")

  elif cmd == "log":
    check_condition(len(args) == 2, "Usage: log <item1,item2,...>")
    model.log_purchase(parse_list(args[1]))

  elif cmd == "next":
    items = get_next_run_items()
    # Group by store
    grouped = defaultdict(list)
    for entry in items:
      grouped[entry["store"]].append(entry["item"])
    # Print as nested lists
    for store_name, item_names in grouped.items():
      print(f"- {store_name}")
      for item_name in item_names:
        item = next((i for i in model.items if i.name == item_name), None)
        if not item:
          # Unexpected but LLMs may hallucinate
          continue
        if item.purchased:
          last_purchase_date = item.purchased[-1]
          print(f"  - {item.name} (last purchased {last_purchase_date})")
        else:
          print(f"  - {item.name}")

  else:
    raise ValueError("Unknown command")


def run_item_edit_prompt(model: Model, name: str):
  item = next((i for i in model.items if i.name == name), None)
  if item == None:
    raise ValueError(f"Item {name} does't exist.")
  print(f"Editing item '{name}'. Type 'done' to finish.")

  while True:
    try:
      user_input = input(f"Editing {name} > ").strip()
    except EOFError:
      print()
      break

    if user_input == "done":
      break

    # Normalize the input: split using regex to capture field/operator/value
    match = re.match(r"^(stores|interval_weeks)\s*(\+?=?\-?=)\s*(.+)$", user_input)
    if not match:
      print(
        "Unrecognized user_input. Use 'stores [+/-]= <store1,store2,...>', 'interval_weeks = <int>', or 'done'."
      )
      continue

    field, operator, value = match.groups()
    field = field.strip()
    operator = operator.strip()
    value = value.strip()

    try:
      if field == "stores":
        new_stores = parse_list(value)
        if operator == "+=":
          model.add_item_stores(name, new_stores)
        elif operator == "-=":
          model.remove_item_stores(name, new_stores)
        elif operator == "=":
          model.update_item_stores(name, new_stores)
        else:
          print("Invalid operator for 'stores'. Use '=', '+=', or '-='.")
      elif field == "interval_weeks":
        if operator != "=":
          print("Only '=' is allowed for interval_weeks.")
          continue
        model.update_item_interval(name, int(value))
      else:
        print("Invalid field. Only 'stores' and 'interval_weeks' are editable.")
    except Exception as e:
      print("Error:", e)


def main():
  model = Model()
  if sys.stdin.isatty():
    print("Welcome to Errands CLI (type 'help' for commands)")
    while True:
      try:
        line = input("> ")
        execute_command(model, line)
      except EOFError:
        print("\nExiting.")
        break
      except KeyboardInterrupt:
        print("\nInterrupted.")
        break
      except Exception as e:
        print("Error:", e)
        print("Type 'help' to see a list of commands.")

  else:
    try:
      for line in sys.stdin:
        execute_command(model, line.strip())
    except Exception as e:
      print("Error:", e)


if __name__ == "__main__":
  main()
