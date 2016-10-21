from wtforms.widgets import html_params


class FileInput(object):
    """
    Renders an updatable file input element

    HTML5 elements do not allow pre-existing values so we created
    this widget to the user feedback as to what was previously
    entered, with the option to clear/change the value.

    Two HTML inputs are generated from this widget named:
        FIELDNAME:previous -- The checkbox to control the previous value
        FIELDNAME:new -- The input element to update the value

    Design note: we decided to keep templates in line to maintain the style
                 of the wtforms codebase


    See: formentry.js on the dynamic handling portion of this widget
    """

    def __call__(self, field, **kwargs):

        if field.data:
            previous_markup = """
            <label><input {attr} /> {field.data.file_name}</label>
            """.format(
                field=field,
                attr=html_params(**{
                    'id': field.id + '-previous',
                    'class_': 'js-fileinput-previous',
                    'type': 'checkbox',
                    'name': field.name + '-previous',
                    'value': '1',
                    'checked': True,
                    'data-fileinput-new': '#{}-new'.format(field.id)
                }))

        else:
            previous_markup = ''

        upload_markup = '<input {attr} />'.format(
            attr=html_params(**{
                'id': field.id + '-new',
                'type': 'file',
                'name': field.name + '-new',
                'class_': 'file js-fileinput-new',
                'data-initial-caption': 'Upload new file...',
                'data-show-upload': 'false',
                'data-show-preview': 'false',
                'data-fileinput-previous': '#{}-previous'.format(field.id)
            }))

        markup = previous_markup + upload_markup

        return markup
