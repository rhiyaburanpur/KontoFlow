RULES = [
    ("Income",      ["upi/cr", "neft", "imps/cr", "transfer from"]),
    ("Reversal",    ["upi/rev"]),
    ("Transport",   ["petro", "fuel", "diesel", "uber", "ola", "rapido", "metro"]),
    ("Food",        ["zomato", "swiggy", "restaurant", "cafe", "food", "kitchen"]),
    ("Groceries",   ["mart", "grocery", "bigbasket", "blinkit", "dmart", "supermarket"]),
    ("Utilities",   ["electric", "water", "gas", "bescom", "mseb", "tata power", "contr"]),
    ("Shopping",    ["amazon", "flipkart", "myntra", "shop", "store"]),
    ("Transfer",    ["upi/dr", "transfer to"]),
]

FALLBACK_CATEGORY = "Other"


def categorize(description: str) -> str:
    """
    Accepts a cleaned transaction description string and returns a category label.

    How it works:
    - Converts the description to lowercase so matching is case-insensitive.
    - Iterates through RULES in order. The first rule whose keyword is found
      anywhere in the description wins.
    - If no rule matches, returns the FALLBACK_CATEGORY.

    The order of RULES matters. More specific rules (Income, Reversal)
    are placed before broader ones (Transfer) so they are matched first.
    For example, "upi/cr" must be checked before "upi/dr" because a
    credit description contains neither "dr" nor "rev".
    """
    lowered = description.lower()

    for category, keywords in RULES:
        for keyword in keywords:
            if keyword in lowered:
                return category

    return FALLBACK_CATEGORY