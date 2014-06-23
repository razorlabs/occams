
def list(request):
    pass

def crap():
    class IOccamsFormComponent(zope.interface.Interface):
        """
        Marker interfaces for interfaces of this plug-in
        """



    class IEditableField(IOccamsFormComponent):
        """
        The human-friendly form for edidting a field.
        """

        # Note we did not make this readonly so that users with superpowers can
        # change it
        name = zope.schema.ASCIILine(
            title=_(u'Variable Name'),
            description=_(
                u'Internal variable name, this value cannot be changed once it is '
                u'created.'
                ),
            )

        title = zope.schema.TextLine(
            title=_(u'Label'),
            description=_(u'The prompt for the user.'),
            )

        description = zope.schema.Text(
            title=_(u'Description'),
            description=_(u'A short description about the field\'s purpose.'),
            required=False,
            )

        order = zope.schema.Int(
            title=_(u'Order'),
            description=_(u'The field\'s order in the form'),
            required=True
            )



    class ICollectable(IOccamsFormComponent):

        is_collection = zope.schema.Bool(
            title=_(u'Multiple?'),
            description=_(u'If selected, the user may enter more than one value.'),
            default=False,
            )


    class IRequireable(IOccamsFormComponent):

        is_required = zope.schema.Bool(
            title=_(u'Required?'),
            description=_(u'If selected, the user will be required to enter a value.'),
            default=False,
            )


    class IEditableChoice(IOccamsFormComponent):

        title = zope.schema.TextLine(
            title=_(u'Displayed Label'),
            )

        value = zope.interface.Attribute(_(u'The value stored for the answer choice'))


    class IEditableBooleanChoice(IEditableChoice):

        value = zope.schema.Bool(
            title=_(u'Stored Value'),
            )


    class IEditableBooleanField(IEditableField, IRequireable):

        choices = zope.schema.List(
            title=_(u'Configure True/False Labels'),
            value_type=DictRow(schema=IEditableBooleanChoice),
            required=True,
            )


    class IEditableDateField(IEditableField, IRequireable):

        pass


    class IEditableDateTimeField(IEditableField, IRequireable):

        pass


    class IEditableIntegerChoice(IEditableChoice):

        value = zope.schema.Int(
            title=_(u'Stored Value'),
            )


    class IEditableIntegerField(IEditableField, IRequireable):

        choices = zope.schema.List(
            title=_(u'Value Constraints'),
            description=_(
                u'If you want the field to be limited to a subset of possible values, '
                u'please enter them below. Leave blank otherwise.'),
            value_type=DictRow(schema=IEditableIntegerChoice),
            required=False,
            )


    class IEditableDecimalChoice(IEditableChoice):

        value = zope.schema.Decimal(
            title=_(u'Stored Value'),
            )


    class IEditableDecimalField(IEditableField, IRequireable):

        choices = zope.schema.List(
            title=_(u'Value Constraints'),
            description=_(
                u'If you want the field to be limited to a subset of possible values, '
                u'please enter them below. Leave blank otherwise.'),
            value_type=DictRow(schema=IEditableDecimalChoice),
            required=False,
            )


    class IEditableStringChoice(IEditableChoice):

        value = zope.schema.TextLine(
            title=_(u'Stored Value'),
            )


    class IEditableStringField(IEditableField, IRequireable, ICollectable):

        choices = zope.schema.List(
            title=_(u'Value Constraints'),
            description=_(
                u'If you want the field to be limited to a subset of possible values, '
                u'please enter them below. Leave blank otherwise.'),
            value_type=DictRow(schema=IEditableStringChoice),
            required=False,
            )


    class IEditableTextField(IEditableField, IRequireable):

        pass


    class IEditableBlobField(IEditableField, IRequireable):

        pass


    class IEditableObjectField(IEditableField):

        pass


    typeInputSchemaMap = dict(
        boolean=IEditableBooleanField,
        date=IEditableDateField,
        datetime=IEditableDateTimeField,
        decimal=IEditableDecimalField,
        integer=IEditableIntegerField,
        string=IEditableStringField,
        text=IEditableTextField,
        blob=IEditableBlobField,
        object=IEditableObjectField,
        )

def view(request):

    class FieldPreview(StandardWidgetsMixin, DisabledMixin, z3c.form.form.Form):
        """
        Preview of form fields for re-rendering single fields during form editing
        """

        ignoreRequest = True

        @property
        def label(self):
            return 'Preview: %s' % self.context.item.name

        def getContent(self):
            return self.context.data

        def update(self):
            self.request.set('disable_border', True)
            schemaField = fieldFactory(self.getContent())
            self.fields = z3c.form.field.Fields(schemaField)
            super(FieldPreview, self).update()


    class FieldJsonView(BrowserView):
        """
        JSON view for form fields
        """

        def __call__(self):
            """
            Returns a clean copy of the current state of the field.
            Additionally adds an extra ``view`` field in the JSON object
            for rendering the field on the client side
            """
            data = copy(self.context.data)
            if data['schema']:
                del data['schema']
            # For client-side ajax update of the field
            if data['type'] != 'object':
                data['view'] = FieldPreview(self.context, self.request)()
            else:
                data['view'] = None
            # JSON doesn't understand dates, gotta clean that up too
            # Cleanup choice values (in case they're decimals)
            if data['choices']:
                for choice in data['choices']:
                    if isinstance(choice['value'], Decimal):
                        choice['value'] = str(choice['value'])

            self.request.response.setHeader(u'Content-type', u'application/json')
            return json.dumps(data)


def add(request):
    class FieldFormInputHelper(object):
        """
        Helper class for displaying the inputs for editing field metadata.
        """

        def getType(self):
            """
            Sub classes must return the value type they are editing
            """
            raise NotImplementedError

        def getMetadataFields(self):
            """
            Configures fields based on type
            """
            if not hasattr(self, '_fields'):
                type_ = self.getType()
                schema = typeInputSchemaMap[type_]
                fields = z3c.form.field.Fields(schema).select('name', 'title', 'description')
                fields['description'].widgetFactory = TextAreaFieldWidget
                if 'choices' in schema:
                    fields += z3c.form.field.Fields(schema).select('choices')
                    fields['choices'].widgetFactory = DataGridFieldFactory
                fields += z3c.form.field.Fields(schema).omit('name', 'title', 'description', 'choices')
                self._fields = fields
            return self._fields

        def datagridInitialise(self, subform, widget):
            """
            Callback for configuring grid widgets
            """
            # Booleans are not allowed to have more than two values (duh)
            if self.getType() == 'boolean':
                subform.fields['value'].widgetFactory = TextFieldWidget
                widget.auto_append = False
                widget.allow_insert = False
                widget.allow_delete = False
                widget.allow_reorder = False
            else:
                widget.allow_reorder = True
                widget.auto_append = True
                widget.allow_insert = True
                widget.allow_delete = True

        def datagridUpdateWidgets(self, subform, widgets, widget):
            """
            Callback for updating grid widgets
            """
            # Booleans are special in that their values are known
            if self.getType() == 'boolean':
                widgets['value'].readonly = 'readonly'


    class FieldAddForm(FieldFormInputHelper, z3c.form.form.AddForm):
        """
        Add form for fields.

        Optionally takes a request variable ``order`` to preset where the
        field will be added (otherwise at the end of the form)
        """
        z3c.form.form.extends(z3c.form.form.AddForm)

        prefix = 'add'

        @property
        def label(self):
            return _('New %s Field') % typesVocabulary.getTermByToken(self.typeName).title

        def getType(self):
            return self.__name__.split('-').pop()

        def update(self):
            self.request.set('disable_border', True)
            # Can't add fields to non-object fields
            if IAttributeContext.providedBy(self.context) and \
                    self.context['type'] != 'object':
                raise NotFound()

            self.buttons = self.buttons.select('cancel', 'add')

            self.fields = self.getMetadataFields().omit('order')

            self.fields += z3c.form.field.Fields(zope.schema.ASCIILine(
                __name__='after',
                title=_(u'After which field'),
                required=False,
                ))

            super(FieldAddForm, self).update()

        def updateWidgets(self):
            super(FieldAddForm, self).updateWidgets()

            # Set the order (this is intended for AJAX requests)
            if 'after' in self.request:
                self.widgets['after'].value = str(self.request.get('after', ''))

            self.widgets['after'].mode = HIDDEN_MODE

            # Set the boolean default if not already set
            if self.getType() == 'boolean' and not self.widgets['choices'].value:
                self.widgets['choices'].value = [
                    dict(title=u'True', value=True),
                    dict(title=u'False', value=False),
                    ]

        def createAndAdd(self, data):
            Session = named_scoped_session(self.context.session)
            cleanupChoices(data)

            if IAttributeContext.providedBy(self.context):
                form = self.context.item.object_schema
            else:
                form = self.context.item

            # create the new field and let ``moveField`` automatically sort it
            newAttribute = model.Attribute(
                schema=form,
                name=str(data['name']).lower(),
                title=data['title'],
                description=data['description'],
                type=self.getType(),
                is_collection=data.get('is_collection', False),
                is_required=data.get('is_required', False),
                )

            # create a new sub-schema if the new field is an object
            if newAttribute.type == 'object':
                newAttribute.object_schema = model.Schema(
                    name=form.name + camelize(data['title']),
                    state=form.state,
                    publish_date=form.publish_date,
                    title=data['title'],
                    description=data['description'],
                    is_inline=True
                    )

            # update the column ordering
            moveField(form, newAttribute, data['after'])

            # add choices, if any
            if data.has_key('choices') and data['choices']:
                applyChoiceChanges(newAttribute, data['choices'])

            Session.flush()

            # broadcast new item only after it's been completely configured
            zope.event.notify(zope.lifecycleevent.ObjectCreatedEvent(newAttribute))

            self._newItem = newAttribute
            return newAttribute

        def nextURL(self):
            url = self.context.absolute_url()
            if self._newItem is not None:
                url = os.path.join(url, str(self._newItem.name), '@@json')
            return url

        @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
        def handleCancel(self, action):
            self._finishedAdd = True


def edit(request):
    class FieldEditForm(FieldFormInputHelper, z3c.form.form.EditForm):
        """
        Edit form for field.
        """
        z3c.form.form.extends(z3c.form.form.EditForm)

        prefix = 'edit'

        @property
        def label(self):
            return _(u'Edit: %s') % self.context.__name__

        @property
        def fields(self):
            return self.getMetadataFields()

        def getType(self):
            return self.context['type']

        def getContent(self):
            return self.context.data

        def update(self):
            self.request.set('disable_border', True)
            # Flip the buttons
            self.buttons = self.buttons.select('cancel', 'apply')
            self.buttons['apply'].title = _(u'Apply')
            self.fields['order'].mode = HIDDEN_MODE
            super(FieldEditForm, self).update()

        def updateWidgets(self):
            super(FieldEditForm, self).updateWidgets()
            self.widgets['name'].readonly = 'readonly'

        def applyChanges(self, data):
            """
            Commits changes to the browser session data
            """

            cleanupChoices(data)
            # Now do the default changes
            changes = super(FieldEditForm, self).applyChanges(data)
            if changes:
                Session = named_scoped_session(self.context.session)
                # Get into the heart of the changes
                for changelist in changes.values():
                    ## outputes lists, so go through them:
                    for change in changelist:
                        if change == 'choices':
                            applyChoiceChanges(self.context.item, data[change])
                        else:
                            setattr(self.context.item, change, data[change])
                Session.flush()
            self.context._data = None
            nextUrl = os.path.join(self.context.absolute_url(), '@@json')
            self.request.response.redirect(nextUrl)
            return changes

        @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
        def handleCancel(self, action):
            parent = self.context.getParentNode()
            nextUrl = os.path.join(parent.absolute_url())
            self.request.response.redirect(nextUrl)


    class VariableNameValidator(z3c.form.validator.SimpleFieldValidator):
        """
        Variable name validation
        """

        def validate(self, value):
            super(VariableNameValidator, self).validate(value)

            # We want lower case, so validate as such (will be forced on add)
            value = value.lower()

            # Check proper Python variable name
            if value != symbolize(value):
                raise zope.interface.Invalid(_(u'Not a valid variable name'))


            if value in reservedWords:
                raise zope.interface.Invalid(_(u'Can\'t use reserved programming word'))

            # Avoid duplicate variable names in the subform
            if IAttributeContext.providedBy(self.context):
                schemaData = self.context.data['schema']
            else:
                schemaData = self.context.data
            if value in schemaData['fields']:
                raise zope.interface.Invalid(_(u'Variable name already exists in this subform'))

            # Avaid duplicate names for scalars
            if IAttributeContext.providedBy(self.context):
                schemaData = self.context.aq_parent.data
            else:
                schemaData = self.context.data
            def get_scalar_fields(schema):
                names = set()
                for key, field in schema['fields'].items():
                    if field['type'] == 'object':
                        names.update(get_scalar_fields(field['schema']))
                    else:
                        names.add(key)
                return names
            names = get_scalar_fields(schemaData)
            if value in names:
                raise zope.interface.Invalid(_(u'Variable name already exists in this form'))

    # Limit variable name validation only to add forms, since that's the only time
    # a user is allow to choose a name
    z3c.form.validator.WidgetValidatorDiscriminators(
        validator=VariableNameValidator,
        view=FieldAddForm,
        field=IEditableField['name'],
        )

    class ConstraintValidator(z3c.form.validator.SimpleFieldValidator):
        """
        Field constraints validation
        """

        def validate(self, value):
            super(ConstraintValidator, self).validate(value)
            if value:
                values = [c['value'] for c in value]
                titles = [c['title'] for c in value]
                if len(values) != len(set(values)) or len(titles) != len(set(titles)):
                    raise zope.interface.Invalid(_(
                        u'Only unique values and titles are allowed'
                        ))


    # Limit the contraint validator to only forms that will be dealing with
    # field metadata (add/edit)
    z3c.form.validator.WidgetValidatorDiscriminators(
        validator=ConstraintValidator,
        view=FieldFormInputHelper,
        widget=DataGridField
        )


def move(request):
    class FieldOrderForm(StandardWidgetsMixin, z3c.form.form.Form):
        """
        Form for editing the position of a field in a form.
        """

        @property
        def label(self):
            return _(u'Reorder: %s') % self.context.__name__

        def getContent(self):
            return self.context.data

        def update(self):
            self.request.set('disable_border', True)
            schemaContext = closest(self.context, ISchemaContext)

            self.fields = z3c.form.field.Fields(zope.schema.Choice(
                __name__='target',
                title=_(u'Target Fieldset'),
                description=_(
                    u'The fieldset within the parent form to send the field to.'
                    ),
                values=listFieldsets(schemaContext.data),
                required=False,
                ))

            self.fields += z3c.form.field.Fields(zope.schema.ASCIILine(
                __name__='after',
                title=_(u'After which field'),
                required=False,
                ))

            super(FieldOrderForm, self).update()

        @z3c.form.button.buttonAndHandler(title=_(u'Sort'), name='apply')
        def handleApply(self, action):
            data, errors = self.extractData()
            if errors:
                self.request.response.setStatus(400)
            else:
                (target, after) = (data['target'], data['after'])
                parent = self.context.getParentNode()
                schemaContext = closest(self.context, ISchemaContext)
                sourceForm = parent.item
                Session = named_scoped_session(self.context.session)
                # Get the target form data that the field is going to
                if target:
                    targetForm = schemaContext.item[target]
                else:
                    targetForm = schemaContext.item
                if targetForm == sourceForm:
                    moveField(targetForm, self.context.item, after)
                    self.context._data = None
                elif (self.context.item in targetForm.values()) or (self.context.item.name in targetForm.keys()):
                # Do not allow the field to be moved into another schema if it
                # already contains a field with the same name
                    self.request.response.setStatus(400)
                else:
                    # This item needs to move to a different fieldset
                    field = self.context.item
                    del sourceForm[self.context.item.name]
                    parent._data = None
                    targetForm[field.name] = field
                    moveField(targetForm, field, after)
                    schemaContext._data = None
                    self.context._data = None
                Session.flush()
                self.request.response.setStatus(200)


    def render(self):
        return u''


def delete(request):

    class FieldDeleteForm(StandardWidgetsMixin, z3c.form.form.Form):
        """
        Delete confirmation form for fields.
        """

    #    template = ViewPageTemplateFile('editor_templates/field_delete.pt')

        prefix = 'delete'

        @property
        def label(self):
            return _(u'Delete: %s') % self.context.__name__

        def getContent(self):
            return self.context.data

        def update(self):
            self.request.set('disable_border', True)
            super(FieldDeleteForm, self).update()

        @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
        def handleCancel(self, action):
            self.request.response.setStatus(304);

        @z3c.form.button.buttonAndHandler(_(u'Yes, I\'m sure'), name='delete')
        def handleDelete(self, action):
            Session = named_scoped_session(self.context.session)
            if self.context.item.object_schema:
                Session.delete(self.context.item.object_schema)
            Session.delete(self.context.item)
            Session.flush()
            self.context._data = None
            self.request.response.setStatus(200)


    # Need to wrap the form because of the custom template
    FieldDeleteFormView = plone.z3cform.layout.wrap_form(FieldDeleteForm)


# Helper Methods
def applyChoiceChanges(field, choiceData):
    # Need a helper to add choice changes
    subSession = object_session(field)
    if field.choices:
        def findChoice(value, itemlist):
            for i, item in enumerate(itemlist):
                if item['value'] == value:
                    return itemlist.pop(i)
            return None

        for choice in field.choices:
            choice.order = choice.order + 1000000

        subSession.flush()
        removable = []
        for choice in field.choices:
            newValue = findChoice(choice.value, choiceData)
            if newValue is not None:
                for key, value in newValue.items():
                    setattr(choice, key, value)
            else:
                removable.append(choice)
        for choice in removable:
            # Remove the choice directly since doing so from the
            # choices collection causes bizarre ordering behavior
            subSession.delete(choice)
        subSession.flush()

    for new_choice in choiceData:
        newChoice = model.Choice(
            attribute=field,
            name = str(new_choice['name']),
            title = unicode(new_choice['title']),
            order = new_choice['order'],
            value = unicode(new_choice['value'])
            )
        # Don't interfere with the collection
        subSession.add(newChoice)
    subSession.flush()
    return field


def moveField(form, field, after=None):
    subSession = object_session(form)
    if after is None:
        field.order = 100
    else:
        field.order = form[after].order + 101
    # Move everything that follows
    for formfield in sorted(form.values(), key=lambda i: i.order):
        if formfield != field:
            formfield.order += 100
            if  formfield.order >= field.order:
                formfield.order += 1
    subSession.flush()
    ## ok, we need to reorder everything
    for order, formfield in enumerate(sorted(form.values(), key=lambda i: i.order)):
        formfield.order = order
    subSession.flush()
    return form
