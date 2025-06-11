import llm
from model import Model, Store, Item


def format_item(item: Item) -> str:
  return (
    f"'{item.name}' that should be purchased every '{item.interval_weeks} weeks' from stores '{', '.join(item.stores)}'"
    + (
      " and it was last purchased on '{', '.join(item.purchased)}'"
      if item.purchased
      else " and it was never purchased previously"
    )
  )


def all_items(model: Model) -> str:
  return "\n".join([format_item(i) for i in model.items])


def preferred_stores(model: Model) -> str:
  return ", ".join([s.name for s in model.stores if s.preferred])


def get_prompt(model: Model) -> str:
  return (
    "I have the following items on my regular shopping list.\n"
    "I'll provide how often I need to restock them and dates I previously purchased them, as well as the stores where I can buy them from.\n"
    "I'll also tell you which stores are preferred.\n"
    "Let me know what items I should buy in the next 2 weeks and from what stores.\n"
    "It's important to only output in the following format:\n"
    "<store1>\n"
    "- <item1>\n"
    "- <item2>\n"
    "<store2>\n"
    "- <item3>\n"
    "Below are the shopping list items:\n"
    f"{all_items(model)}\n"
    "And my preferred stores are:\n"
    f"{preferred_stores(model)}\n"
  )

# Setting API KEY in `$LLM_GEMINI_KEY` or `llm keys set gemini`
response = llm.get_model("gemini-2.0-flash").prompt(get_prompt(Model()))

print(response.text())
