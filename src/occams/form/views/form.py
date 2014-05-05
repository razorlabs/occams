from pyramid.view import view_config
from sqlalchemy import func, orm, sql, null, cast, Unicode
from wtforms import StringField, validators, ValidationError

from occams.datastore.utils.sql import group_concat
from occams.datastore import models
from occams.form import _, Session
from occams.form.csrf import CsrfForm


def is_unique_name(form, field):
    name_exists = sql.exists().where(models.Schema.name == field.data.lower())
    if not Session.query(name_exists).one():
        raise ValidationError(_(u'Form name already in use'))


class CreateForm(CsrfForm):

    name = StringField(
        label=_('Schema Name'),
        description=_(
            u'The form\'s system name. '
            u'The name must not start with numbers or contain special '
            u'characters or spaces.'
            u'This name cannot be changed once the form is published.'),
        validators=[
            validators.required(),
            validators.Length(min=3, max=32),
            validators.Regexp(r'[a-zA-Z_][a-zA-Z0-9_]+'),
            is_unique_name])

    title = StringField(
        label=_(u'Form Title'),
        description=_(
            u'The human-readable name users will see when entering data.'),
        validators=[
            validators.required(),
            validators.Length(3, 128)])


@view_config(
    route_name='home',
    renderer='occams.form:templates/form/list.pt',
    permission='form_view')
def list_(request):
    return {}


@view_config(
    route_name='home',
    xhr=True,
    renderer='json',
    permission='form_view')
def list_json(request):
    """
    Lists all forms used by instance.
    """
    InnerSchema = orm.aliased(models.Schema)
    InnerAttribute = orm.aliased(models.Attribute)
    query = (
        Session.query(models.Schema.name)
        .add_column(
            Session.query(
                Session.query(InnerAttribute)
                .join(InnerSchema, InnerAttribute.schema)
                .filter(InnerSchema.name == models.Schema.name)
                .filter(InnerAttribute.is_private)
                .correlate(models.Schema)
                .exists())
            .as_scalar()
            .label('has_private'))
        .add_column(
            Session.query(InnerSchema.title)
            .filter(InnerSchema.name == models.Schema.name)
            .order_by(
                InnerSchema.publish_date == null(),
                InnerSchema.publish_date.desc())
            .limit(1)
            .correlate(models.Schema)
            .as_scalar()
            .label('title'))
        .add_column(
            group_concat(
                func.coalesce(cast(models.Schema.publish_date, Unicode),
                              cast(models.Schema.id, Unicode)),
                ';')
            .label('versions'))
        .group_by(models.Schema.name)
        .order_by(models.Schema.name))

    def jsonify(row):
        values = vars(row)
        versions = sorted(
            row.versions.split(';'),
            key=lambda v: '-' in v and v,
            reverse=True)
        values['versions'] = []
        values['is_new'] = False
        for version in versions:
            values['versions'].append({
                'url': request.route_path('version_view',
                                          form=row.name,
                                          version=version),
                'label': _(u'draft') if '-' not in version else version
            })
        return values

    return [jsonify(r) for r in query]


@view_config(
    route_name='form_add',
    xhr=True,
    permission='form_add',
    renderer='json')
def add(request):
    """
    Allows a user to create a new type of form.
    """
    form = CreateForm(request.POST, csrf_context=request.session)
    if request.method == 'POST' and form.validate():
        schema = models.Schema(name=form.name.data, title=form.title.data)
        Session.add(schema)
        Session.flush()
        # Versions not necessary since this is a brand new form
        return {
            'type': 'content',
            'name': schema.name,
            'has_private': schema.has_private,
            'title': schema.title,
            'is_new': True,
            'versions': [{
                'url': request.route_path('form_view',
                                          form=schema.name,
                                          version=schema.id),
                'label': _(u'draft')
            }]
        }
    return {
        'type': 'form',
        'title': _(u'Create Form'),
        'action': request.route_path('form_add'),
        'method': 'POST',
        'status': 'pending',
        'fields': [{
            'label': f.label.text,
            'description': f.description,
            'required': f.flags.required,
            'input_type': f.widget.input_type,
            'input': f(class_='form-control'),
            'value': f.data,
            'errors': f.errors,
            'order': i
            } for i, f in enumerate(form)],
        'cancel': _(u'Cancel'),
        'submit': _(u'Create'),
    }


def edit(request):

    class FieldsetsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
        """
        Fields editor form.

        A note on sub-objects: There currently seems to be too many caveats
        surrounding object widgets (see ``z3c.form.object``). Given that, we
        will be using z3c group forms to represent sub objects.

        Uses Browser Session for data.
        """

    #    template = ViewPageTemplateFile('editor_templates/schema_fields.pt')

        # This we're rendering disabled fields, we don't need context data or kss
        ignoreContext = True
        ignoreRequest = True

        # The form's fields, initialized in the constructor
        groups = []

        def types(self):
            """
            Template helper for types
            """
            return typesVocabulary

        def update(self):
            """
            Configures fields based on session data
            """
            self.request.set('disable_border', True)
            groups = []
            objectFilter = lambda x: bool(x['schema'])
            orderSort = lambda i: i['order']
            formData = self.context.data

            defaultFieldsetData = dict(interface=formData['name'], schema=formData)
            groups.append(Fieldset(defaultFieldsetData, self.request, self))

            fields = formData['fields']
            objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

            for objectData in objects:
                groups.append(Fieldset(objectData, self.request, self))

            self.groups = groups
            super(FieldsetsForm, self).update()


    class Fieldset(StandardWidgetsMixin, DisabledMixin, z3c.form.group.Group):
        """
        A generic group for fields of type Object to represent as a fieldset.
        This class can also be used for the top level form to be represented as a
        fieldset (has no referencing field).
        """

        @property
        def prefix(self):
            return self.context.get('name') or ''

        @property
        def label(self):
            return self.context.get('title')

        @property
        def description(self):
            return self.context.get('description')

        def fieldData(self, field=None):
            """
            Returns either the data of the fieldset or the specified field
            """
            if field is None:
                data = self.context
            else:
                data = self.context['schema']['fields'][field.__name__]
            return data

        def url(self, field=None):
            # No field within the object specified, process actual object field
            parentUrl = self.parentForm.context.absolute_url()
            parts = [parentUrl]
            if self.prefix:
                parts.append(self.prefix)
            if field:
                fieldData = self.fieldData(field)
                parts.append(fieldData.get('name'))
            return os.path.join(*parts)

        def editUrl(self, field=None):
            """
            Template helper for the edit URL of a field or group
            """
            return os.path.join(self.url(field), '@@edit')

        def deleteUrl(self, field=None):
            """
            Template helper for the delete URL of a field or group
            """
            return os.path.join(self.url(field), '@@delete')

        def type(self, field=None):
            """
            Template helper for retrieving the type of a field or group
            """
            return self.fieldData(field).get('type')

        def update(self):
            fields = z3c.form.field.Fields()
            serializedFields = self.context['schema']['fields'].values()
            for fieldContext in sorted(serializedFields, key=lambda x: x['order']):
                if fieldContext['type'] != 'object':
                    schemaField = fieldFactory(fieldContext)
                    fields += z3c.form.field.Fields(schemaField)
            self.fields = fields
            super(Fieldset, self).update()


    class FormEditForm(StandardWidgetsMixin, z3c.form.form.EditForm):
        """
        Renders the form for editing, using a subform for the fields editor.
        """
    #
    #    template = ViewPageTemplateFile('editor_templates/schema_edit.pt')

        # Certain sub-form components (*cough* datagridfield) don't handle inline
        # validation very well, so we're turning it off on the entire edit for.
        ignoreRequest = True

        # The form's metadata properties (title, description, storage, etcc...)
        fields = z3c.form.field.Fields(IEditableForm).omit('name')

        cancelMessage = _(u'Changes canceled, nothing saved.')

        @property
        def label(self):
            formlabel = 'Edit: ' + self.context.item.title
            formlabel = formlabel + ' -- Draft created by %(user_name)s on %(create_date)s' % dict(
                    user_name=str(self.context.item.create_user.key),
                    create_date=self.context.item.create_date.strftime('%Y/%m/%d'))
            return _(u'%s') % (formlabel)

        def getContent(self):
            return self.context.data

        def update(self):
            """
            Loads form metadata into browser session
            """
            self.request.set('disable_border', True)
            self.request.set('disable_plone.rightcolumn', True)
            self.request.set('disable_plone.leftcolumn', True)
            # Render the fields editor form
            self.fieldsSubForm = FieldsetsForm(self.context, self.request)
            self.fieldsSubForm.update()

            # Continue the z3c form process
            super(FormEditForm, self).update()

        @z3c.form.button.buttonAndHandler(_(u'<< Back to Listing'), name='cancel')
        def handleCancel(self, action):
            repository = closest(self.context, IRepository)
            self.request.response.redirect(repository.absolute_url())

        @z3c.form.button.buttonAndHandler(_(u'Preview'), name='view')
        def handleView(self, action):
            self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@view'))

        def can_discard(self):
            return not self.context.item.publish_date and \
                (self.context.item.create_user.key == getSecurityManager().getUser().getId() or \
                    checkPermission("occams.form.RemoveForm", self.context)
                )

        @z3c.form.button.buttonAndHandler(_(u'Discard Draft'), name='discard', condition=lambda self: self.can_discard())
        def handleDiscard(self, action):
            """
            Discard form changes.
            """
            Session = named_scoped_session(self.context.session)
            Session.delete(self.context.item)
            Session.flush()
            repository = closest(self.context, IRepository)

            self.request.response.redirect(repository.absolute_url())
            IStatusMessage(self.request).add(self.cancelMessage)

        def can_submit(self):
            return (self.context.item.state == 'draft')

        @z3c.form.button.buttonAndHandler(_(u'Submit Draft for Review'), name='submit', condition=lambda self: self.can_submit())
        def handleSubmit(self, action):
            """
            Save the form changes
            """
            data, errors = self.extractData()
            if errors:
                self.status = self.formErrorsMessage
            else:
                Session = named_scoped_session(self.context.session)
                self.context.item.title = unicode(data['title'])
                if data['description']:
                    self.context.item.description = unicode(data['description'])
                self.context.item.state = 'review'
                for attribute in self.context.item.itervalues():
                    if attribute.type == u'object':
                        attribute.object_schema.state = u'review'
                Session.flush()
                repository = closest(self.context, IRepository)
                self.request.response.redirect(repository.absolute_url())
                IStatusMessage(self.request).add(self.successMessage)

        def can_publish(self):
            return checkPermission("occams.form.PublishForm", self.context)  and \
                      not self.context.item.publish_date


        @z3c.form.button.buttonAndHandler(_(u'Publish Draft'), name='publish', condition= lambda self: self.can_publish())
        def handleComplete(self, action):
            """
            Save the form changes
            """
            data, errors = self.extractData()
            if errors:
                self.status = self.formErrorsMessage
            else:
                Session = named_scoped_session(self.context.session)
                publish_date = data['publish_date'] or datetime.date.today()
                uniquePublishQuery = (
                        Session.query(model.Schema)
                        .filter(model.Schema.name == self.context.item.name)
                        .filter(model.Schema.publish_date == publish_date)
                    )
                if uniquePublishQuery.count() > 0:
                    self.request.response.redirect(self.context.absolute_url() + "/@@edit")
                    message = "There is already a version of this form published on %s; Please select a new date." % publish_date.isoformat()
                    IStatusMessage(self.request).add(message)
                else:
                    self.context.item.title = unicode(data['title'])
                    if data['description']:
                        self.context.item.description = unicode(data['description'])
                    self.context.item.state = u'published'
                    self.context.item.publish_date = publish_date
                    for attribute in self.context.item.itervalues():
                        if attribute.type == u'object':
                            attribute.object_schema.state = u'published'
                            attribute.object_schema.publish_date = publish_date
                    Session.flush()
                    repository = closest(self.context, IRepository)
                    self.request.response.redirect(repository.absolute_url())
                    IStatusMessage(self.request).add(self.successMessage)


    # Need to customize the template further, use wrapper
    FormEditFormView = plone.z3cform.layout.wrap_form(FormEditForm)
