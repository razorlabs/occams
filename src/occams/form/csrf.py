from wtforms.ext.csrf import SecureForm


class CsrfForm(SecureForm):

    def generate_csrf_token(self, csrf_context):
        return csrf_context.get_csrf_token()

    def validate_csrf_token(self, field):
        if field.data != field.current_token:
            raise ValueError('Invalid CSRF')
