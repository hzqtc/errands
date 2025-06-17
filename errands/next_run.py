from collections import defaultdict
from datetime import datetime
from itertools import combinations
from model import Model


def get_avg_interval_weeks(dates: list[datetime]) -> int:
  if len(dates) < 2:
    return 0

  intervals = [
    (parsed_dates[i + 1] - parsed_dates[i]).days for i in range(len(parsed_dates) - 1)
  ]

  return sum(intervals) / len(intervals) / 7


def min_hitting_set(lists: list[list[str]]) -> list:
  # Get the universe of all unique elements
  universe = set(e for group in lists for e in group)

  # Try sets of increasing size
  for size in range(1, len(universe) + 1):
    for combo in combinations(universe, size):
      if all(any(elem in combo for elem in group) for group in lists):
        # Found the minimal hitting set
        return list(combo)
  return []


def is_store_preferred(m: Model, store_name: str) -> bool:
  return next(s for s in m.stores if s.name == store_name).preferred


def get_next_run_items(model: Model) -> list:
  stores = model.stores
  next_run_items = []
  for item in model.items:
    if not item.purchased:
      # Ignore items with 0 previously purchase dates
      continue
    purchased_dates = sorted(datetime.strptime(d, "%Y-%m-%d") for d in item.purchased)
    if len(item.purchased) < 4:
      # Use user provided interval if we don't have enough purchase history
      interval = item.interval_weeks
    else:
      # Calculate the avg purchase interval of the last 10 purchases
      interval = get_avg_interval_weeks(purchased_dates)

    weeks_since_last_purchase = (datetime.now() - purchased_dates[-1]).days / 7
    # If the item should be purchased in the next weeks, include it in the next run
    if weeks_since_last_purchase + 2 > interval:
      next_run_items.append(item)

  minimum_stores = min_hitting_set([i.stores for i in next_run_items])
  grouped_items = defaultdict(list)
  for item in next_run_items:
    store_candidates = list(set(item.stores) & set(minimum_stores))
    store = next(( s for s in store_candidates if is_store_preferred(model, s) ), store_candidates[0])
    grouped_items[store].append(item)

  return grouped_items

