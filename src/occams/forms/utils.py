from six import itervalues


def move_item(items, target, new_order):
    target.order = new_order
    for other in itervalues(items):
        if (target.id and other.id != target.id) or other.order >= new_order:
            other.order += 1
