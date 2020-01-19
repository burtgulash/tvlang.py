class Token:

    def __init__(self, T, value):
        self.T = T
        self.value = value

    def __repr__(self):
        return f"({self.value}::{self.T})"

    def __str__(self):
        return str(self.value)


class Value:

    def __init__(self, T, value):
        self.T = T
        self.value = value

    def __repr__(self):
        if self.T == "builtin":
            return f"{self.T}"
        if self.T == "special":
            return f"{self.T}"
        return f"({self.value}::{self.T})"

    def __str__(self):
        return str(self.value)

NIL = Value("nil", "()")
