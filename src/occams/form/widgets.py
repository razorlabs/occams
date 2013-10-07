import colander
import deform


class GroupInputWidget(deform.widget.MappingWidget):

    template = 'groupinput'
    readonly_template = None
    size = None

    before = None
    after = None

