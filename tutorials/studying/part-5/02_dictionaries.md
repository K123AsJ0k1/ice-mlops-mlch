---
technologies: "Dictionaries"
category: "Explanations and use of technology"
difficulty: "Easy"
---

# Dictionaries

## Used material

1. <span id="used-material-1"></span> [Python Dictionaries](https://www.w3schools.com/python/python_dictionaries.asp)

2. <span id="used-material-2"></span> [Python Dictionary](https://www.geeksforgeeks.org/python/python-dictionary/) 

3. <span id="used-material-3"></span> [Dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)

4. <span id="used-material-4"></span> [Python pickle Module](https://www.w3schools.com/python/ref_module_pickle.asp)

5. <span id="used-material-5"></span> [Understanding Python Pickling with example](https://www.geeksforgeeks.org/python/understanding-python-pickling-example/)

6. <span id="used-material-6"></span> [pickle — Python object serialization](https://docs.python.org/3/library/pickle.html)

## Why use Dictionaries? 

Dictionaries are widely used as the main data type in object storage for the following reasons:

- Most common semi-structured data type with native object storage alignment, a decade-long ecosystem, and supported schema evolution (mature)

- Easy way to decouple data from code, manage states with declarative representation, and provide self-described structure (abstracted)

- Widely supported by major programming languages, pipeline tools, and RESTful networks.

This makes dictionaries the default data type that lets us provide details to automation, abstract them away, and interact with them in any system.  

## How to use Dictionaries?

In our use case, we almost always use the standard dictionary |[(1)](#used-material-1), [(2)](#used-material-2), [(3)](#used-material-3)| in the following ways:

- Defining the dictionary

```
scoring_rubric = {
    'reasoning': '', 
    'correctness': 0,
    'relevance': 0,
}
```

- Getting a key value

```
print(scoring_rubric['relevance']) # Most common
print(scoring_rubric.get('relevance', {})) # Less common, but enables setting predefined values if the key doesn't exist 
```

- Creating/modifying a key

```
scoring_rubric['relevance'] = 1
scoring_rubric['faithfulness'] = 1
```

- Iterating the dictionary


```
for key, value in scoring_rubric.items()
    print(key, value)
```

With these methods, we use dictionaries to handle communicated conditionals and data collection in the following ways: 

- Communicated conditionals

```
communicated_dict = object_storage_interaction()

code_states = get_dict_value(communicated_dict)

if not code_states['halted']:
    if not code_states['running'] or not code_states['complete']:
        pass
```

- Data collection

```
collected_data = []
for value in list_values:
    data = {
        "metadata": {
            "dataset": value['dataset-name']
        },
        "wanted-data": {},
        "execution-time-sec": 0.0
    }

    ### Code

    record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
    collected_data(data)
```

The created/edited dictionaries are by default stored using Pickle serialization |[(4)](#used-material-4), [(5)](#used-material-5), [(6)](#used-material-6)| in the following ways: 

- Serializing it into stored data and a file

```
import pickle

scoring_rubric = {
    'reasoning': '', 
    'correctness': 0,
    'relevance': 0,
}

stored_data = pickle.dumps(scoring_rubric)

with open('stored-file.pkl', 'wb') as f:
    pickle.dump(scoring_rubric, f)
```

- Deserializing from stored data and file

```
import pickle

scoring_rubric = pickle.loads(stored_data)

with open('stored-file.pkl', 'rb') as f:
    scoring_rubric = pickle.load(f)
```

## Dictionary Namespaced Mutating Chain of Responsiblity

When using object storage with object immutability, editing an existing object requires deleting the old object and creating a new object with the edited data, which can cause problems for communication dictionaries. For example, if two or more instances interact with the same dictionary object, they may create separate copies to replace the existing object, resulting in data desynchronization that can lead to errors.

There are various solutions to ensure deterministic object editing, with one interaction-specific solution being a Namespaced, Mutating Chain of Responsibility. In this software design pattern, we will create a schema to create a dictionary that is then serially used by multiple actors using conditions, which enable these actors to modify the specific parts of the dictionary either by editing existing values or adding new key-value pairs.

Using conditions to divide areas of responsibility ensures that all actor-object interactions are read-only until conditions are met, enabling their exclusive writing to the dictionary. This is further enabled by creating the smallest necessary dictionary unit, using object containers and paths as namespaces to keep different task objects separate. As a result, we will only need to worry about concurrent writes with less structured data types, which we cover later. 

---