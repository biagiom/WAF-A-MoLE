from manipulations_static import reset_inline_comments, logical_invariant, change_tautologies, swap_int_repr, \
    spaces_to_comments, spaces_to_whitespaces_alternatives, random_case, comment_rewriting, swap_keywords


def run_test_cases(test_func, test_cases):
    for tc in test_cases:
        result = test_func(tc["payload"])
        if result != tc["expected"]:
            print("FAILED TEST CASE based on {}\nPayload: {}\nResult: {}\nExpected: {}\n".format(
                test_func.__name__, tc["payload"], result, tc["expected"]))


def test_reset_inline_comments():

    test_cases = [
        {"payload": "select * /* comment */ from table", "expected": "select * /**/ from table"},
        {"payload": "select * from table/* test */", "expected": "select * from table/**/"},
        {"payload": "/*test*/select * from table", "expected": "/**/select * from table"}
    ]

    run_test_cases(reset_inline_comments, test_cases)


def test_swap_keywords():

    repl_or = {
        # OR
        "||": [" OR ", " or "],
        "OR": ["||", "or"],
        "or": ["OR", "||"]
    }
    repl_and = {
        # AND
        "&&": [" AND ", " and "],
        "AND": ["&&", "and"],
        "and": ["AND", "&&"],
    }

    repl_ne = {
        # Not equals
        "<>": ["!=", " NOT LIKE ", " not like "],
        "!=": ["<>", " NOT LIKE ", " not like "],
        "NOT LIKE": ["!=", "<>", "not like"],
        "not like": ["!=", "<>", "NOT LIKE"],
    }

    repl_eq = {
        # Equals
        "=": [" LIKE ", " like "],
        "LIKE": ["like", "="],
        "like": ["LIKE", "="]
    }

    repl_symbols = {
        "||": [" OR ", " or "],
        "&&": [" AND ", " and "],
        "=": [" LIKE ", " like "],
        "<>": ["!=", " NOT LIKE ", " not like "],
        "!=": ["<>", " NOT LIKE ", " not like "]
    }

    test_payloads_or_and = [
        "select * from table where 1 {} 1",
        "select * from table where 1=1 {} True",  # OR/AND is searched before =
        "select * from table where 'x'='x' {} True",  # OR/AND is searched before =
        "select * from table where 'x'='x'\n{} True",  # OR/AND is searched before =
        "select * from table where 'x'='x' {}\nTrue",  # OR/AND is searched before =
        "select * from table where 'x'='x'\n{}\nTrue"  # OR/AND is searched before =
    ]

    test_payloads_eq_ne = [
        "select x from table where x {} 0",
        "select x from table where x {} 'test'",
        "select x from table where x\n{} 0",
        "select x from table where x {}\n0",
        "select x from table where x\n{}\n0"
    ]

    test_payloads_new = [
        "select * from table where 1{}1"
    ]
    
    test_cases = []
    for test_payloads, replacements in zip([test_payloads_or_and, test_payloads_or_and, test_payloads_eq_ne, test_payloads_eq_ne, test_payloads_new], [repl_or, repl_and, repl_ne, repl_eq, repl_symbols]):
        for payload, (symbol, variants) in zip(test_payloads, replacements.items()):
            test_cases.append({'payload': payload.format(symbol), 'expected': [payload.format(rep) for rep in variants]})

    run_test_cases(swap_keywords, test_cases)


if __name__ == "__main__":
    test_reset_inline_comments()
    test_swap_keywords()
