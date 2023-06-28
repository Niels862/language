from definitions import DefValue, get_default_defs


class Block:
    def __init__(self, script, master):
        self.script = script
        self.master = master
        self.defs = {}
        for statement in self.script:
            statement.master = self

    def execute(self):
        ip = 0
        while ip < len(self.script):
            self.script[ip].execute()
            ip += 1

    def get_def(self, item):
        if not isinstance(item, str):
            return item
        if item in self.defs:
            return self.defs[item]
        if self.master is not None:
            return self.master.get_def(item)
        return DefValue(item)

    def set_def(self, item, value):
        if self.master is not None:
            return self.master.set_def(item, value)
        self.defs[item] = value

    def del_def(self, item):
        if self.master is not None:
            return self.master.del_def(item)
        if item in self.defs:
            definition = self.defs[item]
            del self.defs[item]
            return definition
        raise NameError(f"{item} was not defined")

    def __str__(self):
        return "\n".join(str(statement) for statement in self.script)


class Statement:
    def __init__(self, stmt, master):
        self.stmt = stmt
        self.master = master
        for item in stmt:
            if not isinstance(item, str):
                item.master = self

    def __getitem__(self, index):
        item = self.stmt[index]
        if isinstance(item, str):
            return item
        return item.execute()

    def get(self, index):
        return self.stmt[index]

    def __len__(self):
        return len(self.stmt)

    def __iter__(self):
        return iter(self[i] for i in range(len(self)))

    def is_vargs(self, index):
        return isinstance(self.stmt[index], Statement)

    def get_vargs(self, index):
        return self.stmt[index]

    def execute(self):
        if len(self.stmt) == 0:
            return None
        for i, entry in enumerate(self.stmt):
            definition = self.get_def(entry)
            if not isinstance(definition, Statement) and not isinstance(definition, Block) \
                    and definition.match(self, self.master, i):
                return definition.execute(self, self.master)
        raise SyntaxError(f"Failed to execute: {self}")

    def get_def(self, item):
        return self.master.get_def(item)

    def set_def(self, item, value):
        return self.master.set_def(item, value)

    def del_def(self, item):
        return self.master.del_def(item)

    def __str__(self):
        string = ""
        for i, item in enumerate(self.stmt):
            if i:
                string += " "
            if isinstance(item, Statement):
                string += f"({item})"
            elif isinstance(item, Block):
                string += "{" + str(item) + "}"
            else:
                string += item
        return string
