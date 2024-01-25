import re


def string_tautology():
    """Returns a list of tautologies based on strings.

    Returns:
        (list) : list of string tautologies
    """
    value_a = 'a'
    value_b = 'b'

    tautologies = [
        # Strings - equals
        "'{}'='{}'".format(value_a, value_a),
        "'{}' LIKE '{}'".format(value_a, value_a),
        '"{}"="{}"'.format(value_a, value_a),
        '"{}" LIKE "{}"'.format(value_a, value_a),
        # Strings - not equal
        "'{}'!='{}'".format(value_a, value_b),
        "'{}'<>'{}'".format(value_a, value_b),
        "'{}' NOT LIKE '{}'".format(value_a, value_b),
        '"{}"!="{}"'.format(value_a, value_b),
        '"{}"<>"{}"'.format(value_a, value_b),
        '"{}" NOT LIKE "{}"'.format(value_a, value_b)
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
    occurrences = [m.start() for m in re.finditer(sub, candidate)]
    if not occurrences:
        return candidate

    pos = occurrences[0]

    before = candidate[:pos]
    after = candidate[pos:]
    # after = after.replace(sub, wanted, 1)
    after = re.sub(sub, wanted, after, 1)

    result = before + after
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

    # pos = re.search("(#|-- )", payload)
    pos = re.search(r"\b\w+(\s*(=|!=|<>|>|<|>=|<=)\s*|\s+(?i:like|not like)\s+)\w+\b", payload)

    if not pos:
        # No comments found
        return payload

    pos = pos.start()

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
    string_tautologies_pos = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*=\s*|\s+(?i:like)\s+)(\'|\")\2\5', payload))
    string_tautologies_neg = list(re.finditer(r'(\'|\")([a-zA-Z]{1}[\w#@$]*)\1(\s*(!=|<>)\s*|\s+(?i:not like)\s+)(\'|\")(?!\2)([a-zA-Z]{1}[\w#@$]*)\6', payload))
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
    new_payload = []

    for c in payload:
        c = c.swapcase()
        new_payload.append(c)

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

    symbols = {
        # OR
        "||": [" OR ", " or "],
        " OR ": [" || ", " or "],
        " or ": [" OR ", " || "],
        # AND
        "&&": [" AND ", " and "],
        " AND ": [" && ", " and "],
        " and ": [" AND ", " && "],
        # Not equals
        "<>": ["!=", " NOT LIKE ", " not like "],
        "!=": ["<>", " NOT LIKE ", " not like "],
        " NOT LIKE ": ["!=", "<>", " not like "],
        " not like ": ["!=", "<>", " NOT LIKE "],
        # Equals
        "=": [" LIKE ", " like "],
        " LIKE ": [" like ", "="],
        " like ": [" LIKE ", "="]
    }

    symbols_in_payload = filter_candidates(symbols, payload)

    if not symbols_in_payload:
        return payload

    # Randomly choose symbol
    candidate_symbol = symbols_in_payload[0]
    # Check for possible replacements
    replacements = symbols[candidate_symbol]

    results = []
    for repl in replacements:
        results.append(replace_first(payload, r"{}".format(re.escape(candidate_symbol)), repl))

    return results


def swap_keywords(payload):

    symbols = {
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

    # symbols_in_payload = [s for s in symbols if re.search(r'{}'.format(s), payload)]
    symbols_in_payload = []
    for symbol in symbols:
        if symbol in ["OR", "or", "AND", "and", "LIKE", "like", "NOT LIKE", "not like"]:
            re_pattern = r'\b{}\b'.format(symbol.replace(" ", "\s+"))
        else:
            re_pattern = r"{}".format(re.escape(symbol))
       
        if re.search(re_pattern, payload):
            symbols_in_payload.append((re_pattern, symbol))

    if not symbols_in_payload:
        return payload

    # Randomly choose symbol
    re_pattern, candidate_symbol = symbols_in_payload[0]
    # Check for possible replacements
    replacements = symbols[candidate_symbol]

    results = []
    for replacement in replacements:
        results.append(replace_first(payload, re_pattern, replacement))

    return results
