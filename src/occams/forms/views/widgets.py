import random
from pyramid.view import view_config
import wtforms
import wtforms.widgets.html5

from .. import _


@view_config(
    route_name='widget_list',
    renderer='../templates/widget/list.pt',
    permission='view')
def list_(request):
    """
    Displays supported form widgets for demo purposes
    """
    return {'form': SampleForm(request.POST)}


LIPSUM_SENTENCES = [
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    'Suspendisse semper est non augue tincidunt gravida.',
    'Proin viverra enim id erat iaculis condimentum.',
    'Cras sed arcu blandit, scelerisque libero vel, rhoncus nunc.',
    'Aliquam erat volutpat.',
    ('Ut convallis, velit eget varius bibendum, est orci feugiat neque, '
     'et tincidunt orci leo a nibh.'),
    'Maecenas nec est quam.',
    'Morbi at felis sem.',
    ('Cum sociis natoque penatibus et magnis dis parturient montes, '
     'nascetur ridiculus mus.')
]

random.shuffle(LIPSUM_SENTENCES)


def random_sentence(num=1):
    return ' '.join([random.choice(LIPSUM_SENTENCES) for i in range(num)])


class SampleSection(wtforms.Form):

    var_hidden = wtforms.HiddenField()

    var_date = wtforms.DateField(
        label=_(u'Date'),
        description=random_sentence(3),
        widget=wtforms.widgets.html5.DateInput())

    var_datetime = wtforms.DateField(
        label=_(u'Date Time'),
        description=random_sentence(3),
        widget=wtforms.widgets.html5.DateTimeInput())

    var_number = wtforms.DateField(
        label=_(u'Number'),
        description=random_sentence(3),
        widget=wtforms.widgets.html5.NumberInput())

    var_single_radio = wtforms.SelectField(
        label=_(u'Single Choice: Radio'),
        description=random_sentence(3),
        choices=[(i, s) for i, s in enumerate(LIPSUM_SENTENCES)],
        widget=wtforms.widgets.ListWidget(),
        option_widget=wtforms.widgets.RadioInput())

    var_single_choice_select = wtforms.SelectField(
        label=_(u'Single Choice: Select'),
        description=random_sentence(3),
        choices=[(i, s) for i, s in enumerate(LIPSUM_SENTENCES)])

    var_multiple_choice_checkbox = wtforms.SelectMultipleField(
        label=_(u'Multiple Choice: Checkbox'),
        description=random_sentence(3),
        choices=[(i, s) for i, s in enumerate(LIPSUM_SENTENCES)],
        widget=wtforms.widgets.ListWidget(),
        option_widget=wtforms.widgets.CheckboxInput())

    var_multiple_choice_select = wtforms.SelectMultipleField(
        label=_(u'Multiple Choice: Select'),
        description=random_sentence(3),
        choices=[(i, s) for i, s in enumerate(LIPSUM_SENTENCES)])

    var_file = wtforms.FileField(
        label=_(u'File Attachment'),
        description=random_sentence(3))

    var_string = wtforms.StringField(
        label=_(u'Text'),
        description=random_sentence(3))

    var_string_telephone = wtforms.StringField(
        label=_(u'Text: Telephone'),
        description=random_sentence(3),
        widget=wtforms.widgets.html5.TelInput())

    var_string_email = wtforms.StringField(
        label=_(u'Text: Email'),
        description=random_sentence(3),
        widget=wtforms.widgets.html5.EmailInput())

    var_text = wtforms.TextAreaField(
        label=_(u'Paragraph Text'),
        description=random_sentence(3))


class SampleForm(wtforms.Form):

    var_section = wtforms.FormField(
        SampleSection,
        label=_(u'Section'),
        description=random_sentence(10))
