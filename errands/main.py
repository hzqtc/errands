#!/usr/bin/env python3

from model import Model
import ast
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
  print("  edit item            # Interactive edit mode")
  print("  list stores          # List all stores")
  print("  list items           # List all items")
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
    if args[1] == "store":
      check_condition(len(args) == 3, "Missing store name")
      name = args[2]
      preferred = parse_bool(args[3]) if len(args) > 3 else False
      model.add_store(name, preferred)
    elif args[1] == "item":
      check_condition(len(args) == 3, "Missing item name")
      name = args[2]
      stores = parse_list(args[3])
      interval = int(args[4])
      model.add_item(name, stores, interval)
    else:
      raise ValueError("Unknown add command")

  elif cmd == "delete":
    if args[1] == "store":
      check_condition(len(args) == 3, "Missing store name")
      model.delete_store(args[2])
    elif args[1] == "item":
      check_condition(len(args) == 3, "Missing item name")
      model.delete_item(args[2])
    else:
      raise ValueError("Unknown delete command")

  elif cmd == "edit":
    if args[1] == "store":
      check_condition(len(args) == 4, "Missing store name or preferred")
      name = args[2]
      preferred = parse_bool(args[3])
      model.edit_store(name, preferred)
    elif args[1] == "item":
      check_condition(len(args) >= 3, "Missing item name")
      name = args[2]
      if len(args) == 5:
        stores = parse_list(args[3])
        model.update_item_store(name, stores)
        interval = int(args[4])
        model.edit_item_interval(name, interval)
      else:
        run_item_edit_prompt(model, name)
    else:
      raise ValueError("Unknown edit command")

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
        print(f"- {i.name}: every {i.interval_weeks} weeks at {i.stores}")
    else:
      raise ValueError("Usage: list stores|items")

  else:
    raise ValueError("Unknown command")


def run_item_edit_prompt(model: Model, name: str):
  item = next((i for i in model.items if i.name == name), None)
  if item == None:
    raise ValueError(f"Item {name} does't exist.")
  print(f"Editing item '{name}'. Type 'done' to finish.")
  store_names = {store.name for store in model.stores}

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
        "Unrecognized user_input. Use 'stores += [...]', 'stores -= [...]', 'stores = [...]', 'interval_weeks = <int>', or 'done'."
      )
      continue

    field, operator, value = match.groups()
    field = field.strip()
    operator = operator.strip()
    value = value.strip()

    try:
      if field == "stores":
        # Try to evaluate the value as a literal (list or string)
        parsed = ast.literal_eval(value)
        if isinstance(parsed, str):
          new_stores = [parsed]
        elif isinstance(parsed, list):
          new_stores = parsed
        else:
          raise ValueError("stores must be a string or list of strings")

        # Validate stores exist
        unknown = [s for s in new_stores if s not in store_names]
        if unknown:
          print(f"Unknown store(s): {', '.join(unknown)}")
          continue

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
