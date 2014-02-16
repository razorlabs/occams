def cast_maybe(value, type_):
    if value is not None:
        return type_(value)
