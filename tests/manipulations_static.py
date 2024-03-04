import re
import sqlparse


def string_tautology():
    """Returns a list of tautologies based on strings.

    Returns:
        (list) : list of string tautologies
    """
    value_a = 'a'
    value_b = 'b'

    tautologies = [
        # Strings - equals
        "'{}'='{}'".format(value_a, value_b),
        "'{}' LIKE '{}'".format(value_a, value_b),
        "'{}'='{}'".format(value_a, value_b),
        "'{}' LIKE '{}'".format(value_a, value_b),
        # Strings - not equal
        "'{}'!='{}'".format(value_a, value_b),
        "'{}'<>'{}'".format(value_a, value_b),
        "'{}' NOT LIKE '{}'".format(value_a, value_b),
        "'{}'!='{}'".format(value_a, value_b),
        "'{}'<>'{}'".format(value_a, value_b),
        "'{}' NOT LIKE '{}'".format(value_a, value_b),
    ]

    return tautologies


def num_tautology():
    """Returns a list of tautologies based on numbers.

    Returns:
        (list) : list of numeric tautologies
    """
    value_n = 10

    tautologies = [
        # Numbers - equal
        "{}={}".format(value_n, value_n),
        "{} LIKE {}".format(value_n, value_n),
        # Numbers - not equal
        "{}!={}".format(value_n, value_n + 1),
        "{}<>{}".format(value_n, value_n + 1),
        "{} NOT LIKE {}".format(value_n, value_n + 1),
        "{} IN ({},{},{})".format(value_n, value_n - 1, value_n, value_n + 1),
    ]

    return tautologies


def replace_first(candidate, sub, wanted):
    """Replace the first occurrence of sub inside candidate with wanted.

    Arguments:
        candidate (str) : the string to be modified
        sub (str) 		: regexp containing what to substitute
        wanted (str) 	: the string that will replace sub

    Raises:
        TypeError : bad type passed as arguments

    Returns:
        (str) : the modified string
    """
    occurrences = list(re.finditer(sub, candidate))
    if not occurrences:
        return candidate

    match = occurrences[0]

    before = candidate[:match.start()]
    after = candidate[match.end():]
    result = before + wanted + after
    return result


def filter_candidates(symbols, payload):
    """Return all the symbols that are contained inside the input payload string.

    Arguments:
        symbols (dict)  : dictionary of symbols to filter (using the key)
        payload (str)   : the payload to use for the filtering

    Raises:
        TypeError : bad types passed as argument

    Returns:
        list : a list containing all the symbols that are contained inside the payload.

    """

    return [s for s in symbols.keys() if re.search(r'{}'.format(re.escape(s)), payload)]


def reset_inline_comments(payload: str):
    """Remove first multi-line comment content found in a payload.
    Arguments:
        payload: query payload string

    Returns:
        str: payload modified
    """
    positions = list(re.finditer(r"/\*[^(/\*|\*/)]*\*/", payload))

    if not positions:
        return payload

    pos = positions[0].span()

    replacement = "/**/"

    new_payload = payload[: pos[0]] + replacement + payload[pos[1] :]

    return new_payload


def logical_invariant(payload):
    """logical_invariant

    Adds an invariant boolean condition to the payload

    E.g., something OR False


    :param payload:
    """
    # rule matching numeric tautologies
    num_tautologies_pos = list(re.finditer(r'\b(\d+)(\s*=\s*|\s+(?i:like)\s+)\1\b', payload))
    num_tautologies_neg = list(re.finditer(r'\b(\d+)(\s*(!=|<>)\s*|\s+(?i:not like)\s+)(?!\1\b)\d+\b', payload))
    # rule matching string tautologies
    string_tautologies_pos = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*=\s*|\s+(?i:like)\s+)(\'|\")\2\4', payload))
    string_tautologies_neg = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*(!=|<>)\s*|\s+(?i:not like)\s+)(\'|\")(?!\2)([a-zA-Z]{1}[\w#@$]*)\5', payload))
    results = num_tautologies_pos + num_tautologies_neg + string_tautologies_pos + string_tautologies_neg
    if not results:
        return payload
    candidate = results[0]

    pos = candidate.end()

    replacements = [
        # AND True
        " AND 1",
        " AND True",
        " AND 10=10",
        " AND 'x'='x'",
        # OR False
        " OR 0",
        " OR False",
        " OR 10=11",
        " OR 'x'='y'",
    ]

    results = []
    for replacement in replacements:
        results.append(payload[:pos] + replacement + payload[pos:])

    return results


def change_tautologies(payload):
    # results = list(re.finditer(r'((?<=[^\'"\d\wx])\d+(?=[^\'"\d\wx]))=\1', payload))
    # rules matching numeric tautologies
    num_tautologies_pos = list(re.finditer(r'\b(\d+)(\s*=\s*|\s+(?i:like)\s+)\1\b', payload))
    num_tautologies_neg = list(re.finditer(r'\b(\d+)(\s*(!=|<>)\s*|\s+(?i:not like)\s+)(?!\1\b)\d+\b', payload))
    # rule matching string tautologies
    string_tautologies_pos = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*=\s*|\s+(?i:like)\s+)(\'|\")\2\4', payload))
    string_tautologies_neg = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*(!=|<>)\s*|\s+(?i:not like)\s+)(\'|\")(?!\2)([a-zA-Z]{1}[\w#@$]*)\5', payload))
    results = num_tautologies_pos + num_tautologies_neg + string_tautologies_pos + string_tautologies_neg
    if not results:
        return payload
    candidate = results[0]

    replacements = num_tautology() + string_tautology()
    results = []
    for replacement in replacements:
        results.append(payload[: candidate.span()[0]] + replacement + payload[candidate.span()[1] :])

    return results


def spaces_to_comments(payload):
    # TODO: make it selectable (can be mixed with other strategies)
    symbols = {" ": ["/**/"], "/**/": [" "]}

    symbols_in_payload = filter_candidates(symbols, payload)

    if not symbols_in_payload:
        return payload

    # Randomly choose symbol
    candidate_symbol = symbols_in_payload[0]
    # Check for possible replacements
    replacements = symbols[candidate_symbol]

    results = []
    # Apply mutation at first occurrence in the payload
    for replacement in replacements:
        results.append(replace_first(payload, re.escape(candidate_symbol), replacement))

    return results


def spaces_to_whitespaces_alternatives(payload):

    symbols = {
        " ": ["\t", "\n", "\f", "\v", "\xa0"],
        "\t": [" ", "\n", "\f", "\v", "\xa0"],
        "\n": ["\t", " ", "\f", "\v", "\xa0"],
        "\f": ["\t", "\n", " ", "\v", "\xa0"],
        "\v": ["\t", "\n", "\f", " ", "\xa0"],
        "\xa0": ["\t", "\n", "\f", "\v", " "],
    }

    symbols_in_payload = filter_candidates(symbols, payload)

    if not symbols_in_payload:
        return payload

    # Randomly choose symbol
    candidate_symbol = symbols_in_payload[0]
    # Check for possible replacements
    replacements = symbols[candidate_symbol]

    results = []
    for replacement in replacements:
        # Apply mutation at the first occurrence in the payload
        results.append(replace_first(payload, re.escape(candidate_symbol), replacement))

    return results


def random_case(payload):
    tokens = []
    for t in sqlparse.parse(payload):
        tokens.extend(list(t.flatten()))

    sql_keywords = set(sqlparse.keywords.KEYWORDS_COMMON.keys())
    # sql_keywords = ' '.join(list(sqlparse.keywords.KEYWORDS_COMMON..keys()) + list(sqlparse.keywords.KEYWORDS.keys()))

    # Make sure case swapping is applied only to SQL tokens
    new_payload = []
    for token in tokens:
        if token.value.upper() in sql_keywords:
            new_token = ''.join([c.swapcase() for c in token.value])
            new_payload.append(new_token)
        else:
            new_payload.append(token.value)

    return "".join(new_payload)


def comment_rewriting(payload):

    if "#" in payload or "-- " in payload:
        return payload + "hello"
    elif re.search(r"/\*[^(/\*|\*/)]*\*/", payload):
        return replace_first(payload, r"/\*[^(/\*|\*/)]*\*/", "/*" + "hello" + "*/")
    else:
        return payload


def swap_int_repr(payload):

    # candidates = list(re.finditer(r'(?<=[^\'"\d\wx])\d+(?=[^\'"\d\wx])', payload))
    candidates = list(re.finditer(r'\b\d+\b', payload))

    if not candidates:
        return payload

    candidate_pos = candidates[0].span()

    candidate = payload[candidate_pos[0] : candidate_pos[1]]

    replacements = [
        hex(int(candidate)),
        "(SELECT {})".format(candidate),
        # "({})".format(candidate),
        # "OCT({})".format(int(candidate)),
        # "HEX({})".format(int(candidate)),
        # "BIN({})".format(int(candidate))
    ]

    results = []
    for replacement in replacements:
        results.append(payload[: candidate_pos[0]] + replacement + payload[candidate_pos[1] :])

    return results


def swap_keywords(payload):

    replacements = {
        # OR
        "||": [" OR ", " or "],
        "OR": ["||", "or"],
        "or": ["OR", "||"],
        # AND
        "&&": [" AND ", " and "],
        "AND": ["&&", "and"],
        "and": ["AND", "&&"],
        # Not equals
        "<>": ["!=", " NOT LIKE ", " not like "],
        "!=": ["<>", " NOT LIKE ", " not like "],
        "NOT LIKE": ["!=", "<>", "not like"],
        "not like": ["!=", "<>", "NOT LIKE"],
        # Equals
        "=": [" LIKE ", " like "],
        "LIKE": ["like", "="],
        "like": ["LIKE", "="]
    }

    # Use sqlparse to tokenize the payload in order to better match keywords,
    # even when they are composed by multiple keywords such as "NOT LIKE"
    tokens = []
    for t in sqlparse.parse(payload):
        tokens.extend(list(t.flatten()))

    indices = [idx for idx, token in enumerate(tokens) if token.value in replacements]
    if not indices:
        return [payload]

    target_idx = indices[0]
    # new_payload = "".join([random.choice(replacements[token.value]) if idx == target_idx else token.value for idx, token in enumerate(tokens)])

    results = []
    for repl in replacements[tokens[target_idx].value]:
        results.append("".join([repl if idx == target_idx else token.value for idx, token in enumerate(tokens)]))

    return results
