from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Callable
from datetime import date
import functools
import tomlkit

DATA_FILE = Path("data.toml")


@dataclass
class Store:
  name: str
  preferred: bool = False


@dataclass
class Item:
  name: str
  interval_weeks: int
  stores: List[str] = field(default_factory=list)
  purchased: List[str] = field(default_factory=list)


def autosave(func: Callable):
  """Decorator that saves model data after a mutating method."""

  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    result = func(self, *args, **kwargs)
    self._save_data()
    return result

  return wrapper


class Model:
  def __init__(self):
    self.stores: List[Store] = []
    self.items: List[Item] = []
    self._load_data()

  def _load_data(self):
    if not DATA_FILE.exists():
      return

    with open(DATA_FILE, "r") as fp:
      doc = tomlkit.load(fp)
    self.stores = [Store(**dict(s)) for s in doc.get("stores", [])]
    self.items = [Item(**dict(i)) for i in doc.get("items", [])]

  def _save_data(self):
    doc = tomlkit.document()

    store_aot = tomlkit.aot()
    for s in self.stores:
      t = tomlkit.table()
      t.update(s.__dict__)
      store_aot.append(t)
    doc.append("stores", store_aot)

    item_aot = tomlkit.aot()
    for i in self.items:
      t = tomlkit.table()
      t.update(i.__dict__)
      item_aot.append(t)
    doc.append("items", item_aot)

    with open(DATA_FILE, "w") as fp:
      tomlkit.dump(doc, fp)

  def store_exists(self, name: str) -> bool:
    return any(s.name == name for s in self.stores)

  @autosave
  def add_store(self, name: str, preferred: bool = False):
    if any(s.name == name for s in self.stores):
      raise ValueError(f"Store '{name}' already exists.")
    self.stores.append(Store(name=name, preferred=preferred))

  @autosave
  def delete_store(self, name: str):
    if not any(s.name == name for s in self.stores):
      raise ValueError(f"Store '{name}' does't exist.")
    self.stores = [s for s in self.stores if s.name != name]

  @autosave
  def edit_store(self, name: str, preferred: bool):
    for s in self.stores:
      if s.name == name:
        s.preferred = preferred
        return
    raise ValueError(f"Store '{name}' does't exist.")

  @autosave
  def add_item(self, name: str, store_list: List[str], interval: int):
    if any(i.name == name for i in self.items):
      raise ValueError(f"Item '{name}' already exists.")
    for store in store_list:
      if not self.store_exists(store):
        raise ValueError(f"Store '{store}' does't exist.")
    self.items.append(Item(name=name, stores=store_list, interval_weeks=interval))

  @autosave
  def delete_item(self, name: str):
    if not any(i.name == name for i in self.items):
      raise ValueError(f"Item '{name}' does't exist.")
    self.items = [i for i in self.items if i.name != name]

  @autosave
  def add_item_stores(self, name: str, stores_to_add: List[str]):
    for i in self.items:
      if i.name == name:
        for s in stores_to_add:
          if not self.store_exists(s):
            raise ValueError(f"Store '{s}' does't exist.")
          elif s in i.stores:
            raise ValueError(f"Store '{s}' already exists for item '{i.name}'.")
          else:
            i.stores.append(s)
        return
    raise ValueError(f"Item '{name}' does't exist.")

  @autosave
  def remove_item_stores(self, name: str, stores_to_remove: List[str]):
    for i in self.items:
      if i.name == name:
        for s in stores_to_remove:
          if s not in i.stores:
            raise ValueError(f"Store '{s}' does't exist for item '{i.name}")
          else:
            i.stores.remove(s)
        return
    raise ValueError(f"Item '{name}' does't exist.")

  @autosave
  def update_item_stores(self, name: str, stores: List[str]):
    for s in stores:
      if not self.store_exists(s):
        raise ValueError(f"Store '{s}' does't exist.")
    for i in self.items:
      if i.name == name:
        i.stores = stores
        return
    raise ValueError(f"Item '{name}' does't exist.")

  @autosave
  def update_item_interval(self, name: str, interval: int):
    for i in self.items:
      if i.name == name:
        i.interval_weeks = interval
        return
    raise ValueError(f"Item '{name}' does't exist.")

  @autosave
  def log_purchase(self, item_names: List[str], purchase_date: date = None):
    if purchase_date is None:
      purchase_date = date.today()
    purchase_date_str = purchase_date.strftime("%Y-%m-%d")
    for name in item_names:
      name_found: bool = False
      for i in self.items:
        if i.name == name:
          name_found = True
          # Dedup with the last purchase date
          if i.purchased == [] or purchase_date_str != i.purchased[-1]:
            i.purchased.append(purchase_date_str)
          break
      if not name_found:
        raise ValueError(f"Item '{name}' does't exist.")
