from random import randint


class DefBase:
    def __init__(self, callback):
        self.callback = callback

    def match(self, stmt, program, place):
        return False

    def execute(self, stmt, program):
        return self.callback(stmt, program)

    def __str__(self):
        return "<?>"


class DefPrefixUnary(DefBase):
    def __init__(self, callback):
        super().__init__(callback)

    def match(self, stmt, program, place):
        return len(stmt) == 2 and place == 0

    def __str__(self):
        return "<Prefix Unary>"


class DefPrefixVArgs(DefBase):
    def __init__(self, callback):
        super().__init__(callback)

    def match(self, stmt, program, place):
        return place == 0

    def __str__(self):
        return "<Prefix VArgs>"


class DefInfixBinary(DefBase):
    def __init__(self, callback):
        super().__init__(callback)

    def match(self, stmt, program, place):
        return len(stmt) == 3 and place == 1

    def __str__(self):
        return "<Infix Binary>"


class DefInfixBinaryOperation(DefInfixBinary):
    def __init__(self, operation, num_only=True):
        super().__init__(self.callback)
        self.operation = operation
        self.num_only = num_only

    def callback(self, stmt, program):
        left = program.get_def(stmt[0])
        right = program.get_def(stmt[2])
        if not isinstance(left, DefValue) or not isinstance(right, DefValue):
            raise ValueError("Expected Values")
        try:
            left = int(left.value)
        except ValueError:
            left = left.value
        try:
            right = int(right.value)
        except ValueError:
            right = right.value
        if self.num_only and (not isinstance(left, int) or not isinstance(right, int)):
            raise ValueError("Expected Numbers")
        return DefValue(str(self.operation(left, right)))


class DefValue(DefBase):
    def __init__(self, value):
        super().__init__(lambda stmt, program: value)
        if value.startswith("0b") and len(value) > 2 and all(c in "01" for c in value[2:]):
            self.value = str(int(value[2:], 2))
        elif value.startswith("0x") and len(value) > 2 and all(c.lower() in "01234567890abcdef" for c in value[2:]):
            self.value = str(int(value[2:], 16))
        else:
            self.value = value

    def match(self, stmt, program, place):
        return len(stmt) == 1

    def __str__(self):
        return self.value

    def __bool__(self):
        return self.value not in ["", "0"]


class DefFunc(DefBase):
    def __init__(self, args, block):
        super().__init__(lambda *v: 0)
        self.args = args
        self.block = block


class DefBlock(DefBase):
    def __init__(self, callback, stmt_format):
        super().__init__(callback)
        self.stmt_format = stmt_format

    def match(self, stmt, program, place):
        return self.stmt_format(stmt, program, place)


def boolstring(value):
    return "1" if value else "0"


def cb_assign(stmt, program):
    if stmt.is_vargs(0) and not stmt.is_vargs(2):
        if len(stmt.get_vargs(0)) == 0:
            raise ValueError("Expected VArgs > 0")
        for item in stmt.get_vargs(0):
            program.set_def(item, program.get_def(stmt[2]))
    elif stmt.is_vargs(0) and stmt.is_vargs(2):
        i = 0
        defs = [program.get_def(item) for item in stmt.get_vargs(2)]
        if len(stmt.get_vargs(0)) == 0 or len(defs) == 0:
            raise ValueError("Expected VArgs > 0")
        for item in stmt.get_vargs(0):
            program.set_def(item, defs[i])
            i = (i + 1) % len(defs)
    else:
        return program.set_def(stmt.get(0), program.get_def(stmt[2]))
    return program.get_def(stmt.get_vargs(0)[0])


def cb_delete(stmt, program):
    if stmt.is_vargs(1):
        for item in stmt.get_vargs(1):
            program.del_def(item)
    else:
        program.del_def(stmt[1])
    return DefValue("")


def cb_print(stmt, program):
    for i in range(1, len(stmt)):
        if i > 1:
            print(" ", end="")
        print(program.get_def(stmt[i]), end="")
    print()
    return DefValue("")


def cb_input(stmt, program):
    if not isinstance(stmt[1], str):
        raise ValueError("Expected String")
    program.set_def(stmt[1], DefValue(input("> ")))


def cb_while(stmt, program):
    while stmt[1]:
        _ = stmt[2]


def cb_if(stmt, program):
    if stmt[1]:
        _ = stmt[2]


def cb_if_else(stmt, program):
    if stmt[1]:
        _ = stmt[2]
    else:
        _ = stmt[3]


def cb_using(stmt, program):
    if stmt[1] == "all":
        program.defs = get_default_defs() | program.defs
    else:
        raise SyntaxError("??")


def cb_at(stmt, program):
    left = program.get_def(stmt[0])
    right = program.get_def(stmt[2])
    if not isinstance(left, DefValue) or not isinstance(right, DefValue):
        raise ValueError("Expected Value")
    try:
        index = int(right.value)
    except ValueError:
        raise ValueError("Expected Number")
    value = left.value
    if value.startswith("[") and value.endswith("]"):
        array = value[1:-1].split(",")
        return array[index % len(array)].strip()
    return DefValue(value[index % len(value)])


def cb_for(stmt, program):
    _ = stmt[1]
    while stmt[2]:
        _ = stmt[4]
        _ = stmt[3]


def cb_lengthof(stmt, program):
    value = program.get_def(stmt[1])
    if not isinstance(value, DefValue):
        raise ValueError("Expected Value")
    value = value.value
    if value.startswith("[") and value.endswith("]"):
        return len(value.split(","))
    return DefValue(str(len(value)))


def cb_func(stmt, program):
    name = stmt.get(1)
    if not isinstance(name, str):
        raise ValueError("Function name should be string")
    args = []
    for arg in stmt.get(2):
        if not isinstance(arg, str):
            raise ValueError("Function arg name should be string")
        args.append(arg)
    program.set_def(name, DefFunc(name, args))


def cb_random(stmt, program):
    value = program.get_def(stmt[1])
    if not isinstance(value, DefValue):
        raise ValueError("Expected Value")
    try:
        value = int(value.value)
    except ValueError:
        raise ValueError("Expected Number")
    return DefValue(str(randint(0, value)))


def op_add(left, right):
    if isinstance(left, int) and isinstance(right, int):
        return left + right
    return str(left) + str(right)


def op_sub(left, right):
    if isinstance(left, int) and isinstance(right, int):
        return left - right
    left, right = str(left), str(right)
    while right in left:
        index = left.find(right)
        left = left[:index] + left[index + len(right):]
    return left


def get_default_defs():
    return {
        "=": DefInfixBinary(cb_assign),
        "delete": DefPrefixUnary(cb_delete),
        "#": DefPrefixVArgs(lambda stmt, program: None),
        "print": DefPrefixVArgs(cb_print),
        "input": DefPrefixUnary(cb_input),
        "+": DefInfixBinaryOperation(op_add, False),
        "-": DefInfixBinaryOperation(op_sub, False),
        "*": DefInfixBinaryOperation(lambda left, right: left * right),
        "/": DefInfixBinaryOperation(lambda left, right: left // right),
        "%": DefInfixBinaryOperation(lambda left, right: left % right),
        "^": DefInfixBinaryOperation(lambda left, right: left**right),
        "<": DefInfixBinaryOperation(lambda left, right: boolstring(left < right), False),
        ">": DefInfixBinaryOperation(lambda left, right: boolstring(left > right), False),
        "<=": DefInfixBinaryOperation(lambda left, right: boolstring(left <= right), False),
        ">=": DefInfixBinaryOperation(lambda left, right: boolstring(left >= right), False),
        "==": DefInfixBinaryOperation(lambda left, right: boolstring(left == right), False),
        "!=": DefInfixBinaryOperation(lambda left, right: boolstring(left != right), False),
        "&&": DefInfixBinaryOperation(lambda left, right: boolstring(left and right), False),
        "||": DefInfixBinaryOperation(lambda left, right: boolstring(left or right), False),
        "while": DefBlock(cb_while, lambda stmt, program, place: len(stmt) == 3 and place == 0),
        "if": DefBlock(cb_if, lambda stmt, program, place: len(stmt) == 3 and place == 0),
        "if_else": DefBlock(cb_if_else, lambda stmt, program, place: len(stmt) == 4 and place == 0),
        "true": DefValue("1"),
        "false": DefValue("0"),
        "using": DefPrefixUnary(cb_using),
        "at": DefInfixBinary(cb_at),
        "for": DefBlock(cb_for, lambda stmt, program, place: len(stmt) == 5 and place == 0),
        "lengthof": DefPrefixUnary(cb_lengthof),
        "none": DefValue(""),
        "func": DefBlock(cb_func, lambda stmt, program, place: len(stmt) == 4 and place == 0),
        "random": DefPrefixUnary(cb_random)
     }
