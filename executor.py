from program import Block, Statement
from definitions import get_default_defs


def tokenize(program):
    tokens = [""]
    is_string = False
    is_array = False
    for char in program:
        if is_string and char != "\"":
            tokens[-1] += char
        elif char == "[":
            is_array = True
            tokens.append("[")
        elif char == "]":
            is_array = False
            tokens[-1] += "]"
        elif char == "(" or char == ")" or char == "{" or char == "}" or char == ";":
            tokens.append(char)
            tokens.append("")
        elif char == "\"":
            is_string = not is_string
        elif not is_array and (char in [" ", "\t", ",", "\n"]):
            tokens.append("")
        else:
            tokens[-1] += char
    return list(filter(lambda c: c and c != "\\", tokens))


def get_token(tokens):
    if len(tokens) > 0:
        return tokens[0]
    return ";"


def eat_token(tokens):
    if len(tokens) > 0:
        return tokens.pop(0)
    return ";"


def parse_statement(tokens):
    statement = []
    token = get_token(tokens)
    while token not in [";", ")"]:
        if token == "(":
            eat_token(tokens)
            statement.append(parse_statement(tokens))
        elif token == "{":
            eat_token(tokens)
            statement.append(parse_block(tokens))
        else:
            statement.append(eat_token(tokens))
        token = get_token(tokens)
    eat_token(tokens)
    return Statement(statement, None)


def parse_block(tokens):
    statements = []
    while len(tokens) > 0 and get_token(tokens) != "}":
        statements.append(parse_statement(tokens))
    eat_token(tokens)
    return Block(statements, None)


def execute(code):  # script = collection of stmts, stmt = collection of words
    program = parse_block(tokenize(code))
    program.defs = get_default_defs()
    program.execute()
