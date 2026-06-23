# ── 1. LIST  [ordered, changeable, duplicates allowed] ──────
fruits = ["apple", "banana", "apple", "mango"]
fruits.append("orange")      # add to end
fruits.insert(1, "grape")    # add at index
fruits.remove("banana")      # remove by value
fruits.pop()                 # remove last item
fruits[0] = "kiwi"           # update
print(fruits[0])             # access by index
print(len(fruits))           # length


# ── 2. TUPLE  (ordered, unchangeable, duplicates allowed) ───
location = (19.07, 72.87)
print(location[0])           # access by index → 19.07
# location[0] = 10           # Error! Can't modify a tuple
single = (42,)               # single-element tuple needs a comma


# ── 3. DICTIONARY  {key: value, no duplicate keys} ──────────
person = {"name": "Rahul", "age": 25, "city": "Mumbai"}
print(person["name"])        # access by key → Rahul
person["age"] = 26           # update value
person["job"] = "Dev"        # add new key
del person["city"]           # delete key
print(person.keys())         # all keys
print(person.values())       # all values
print(person.get("name"))    # safe access (no KeyError)


# ── 4. SET  {unique values, unordered, no index access} ─────
tags = {"python", "coding", "python", "dev"}
print(tags)                  # duplicates auto-removed
tags.add("ai")               # add item
tags.remove("dev")           # remove item
tags.discard("xyz")          # remove safely (no error if missing)

# Set operations
a = {1, 2, 3}
b = {3, 4, 5}
print(a | b)                 # union    → {1,2,3,4,5}
print(a & b)                 # intersection → {3}
print(a - b)                 # difference  → {1,2}


# ── QUICK COMPARISON ────────────────────────────────────────
# Feature       List    Tuple   Dict        Set
# Ordered       ✅      ✅      ✅(3.7+)    ❌
# Changeable    ✅      ❌      ✅          ✅
# Duplicates    ✅      ✅      ❌(keys)    ❌
# Access by     index   index   key         —
# Syntax        [ ]     ( )     { : }       { }

# WHEN TO USE?
# List  → ordered collection you'll modify
# Tuple → fixed data (coordinates, RGB, DB records)
# Dict  → look up values by name/key
# Set   → unique items, fast membership check
