# 🛒 errands

**errands** is a smart, terminal-based grocery list manager that helps you track stores, shopping intervals, and mostly important what items need restock on your next run.

It uses a TOML file for storing stores, grocery items and purchase history data and uses AI to recommend what you need to restock.

---

## 📦 Installation

Make sure you have Python 3.10+.

```bash
git clone https://github.com/yourusername/errands.git
cd errands
uv sync
```

## 🚀 Usage

Start the interactive shell:

```bash
uv run errands/main.py
```

Or add data by editing data.toml directly:

```bash
vim data.toml
```

## 🧠 AI Assistance

The `next_run` command uses an LLM to analyze purchase history and stocking intervals, then suggests what needs restocking in the next 2 weeks.

## 🧾 Commands

```
add store <name> <preferred: true|false>
    Add a store with an optional preferred flag.

delete store <name>
    Remove a store by name.

edit store <name> <preferred: true|false>
    Update the 'preferred' setting for a store.

add item <name> <[stores]> <interval_weeks>
    Add an item with a list of stores and a stocking interval.

delete item <name>
    Remove an item by name.

edit item <name> <[stores]> <interval_weeks>
    Update stores and stocking interval for an item.

edit item
    (TBD - possibly interactive item editor)

list stores
    Show all stores, including which are preferred.

list items
    Show all items, including intervals and purchase history.

log_purcahse <item1> <item2> ...
    Record a purchase event for one or more items (uses today’s date).

next_run
    Suggest items to restock in the next 2 weeks (uses AI).

help
    Show this help message.

exit
    Quit the interactive shell.
```

## 📁 Data Format

All data is stored in a data.toml file using TOMLKit, and automatically saved after every change.


## ✅ Roadmap Ideas
  - Date statistics (how often something actually gets bought)
  - Store discouns integration

