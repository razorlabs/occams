"""
Placeholder for future data entry views.
"""
from datetime import date, datetime
from Products.statusmessages.interfaces import IStatusMessage
import plone.z3cform.layout
from z3c.form.interfaces import DISPLAY_MODE, INPUT_MODE
from z3c.saconfig import named_scoped_session
import z3c.form.group
import z3c.form.button
import z3c.form.field
import z3c.form.browser
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import implements
from zope.schema.interfaces import IField
from zope.event import notify

from zope.lifecycleevent import modified

from occams.form.traversal import closest
from plone.memoize import view
from sqlalchemy.orm import object_session
from sqlalchemy.orm.exc import NoResultFound
from zope.app.pagetemplate import viewpagetemplatefile

from occams.form import MessageFactory as _
from occams.form import interfaces
from occams.datastore import model
from occams.form.entry import EntityMovedEvent

def DynamicChoiceWidget(field, request):
    """
    An Adapter that returns a Radio Widget if the number of choices is less
    than 4, otherwise returns a Select Widget
    """
    try:
        if hasattr(field, 'vocabulary') and field.vocabulary and len(field.vocabulary) < 4:
            return z3c.form.browser.radio.RadioFieldWidget(field, request)
        return z3c.form.browser.select.SelectFieldWidget(field, request)
    except TypeError:
        ## This vocabulary has no length?!?!
        return z3c.form.browser.select.SelectFieldWidget(field, request)

class DataEntryGroup(z3c.form.group.Group):
    """
    """
    implements(interfaces.IDataEntryForm)
    data = None
    def getContent(self):
        data = self.context.get('data', getattr(self.context, 'data', None))
        if data:
            for name in self.__name__.split('.'):
                data = data.get(name, {})
        else:
            data = {}
        return data

class DataForm(object):
    """
    Base form for shared
    """
    enable_form_tabbing = False

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

    def getPreFields(self):
        """
        Fields that should appear before the EAV Fields
        """
        return z3c.form.field.Fields()

    def getPreGroups(self):
        """
        Group Fields that should appear before the EAV Fields
        """
        return []

    def getPostGroups(self):
        """
        Group Fields that should appear after the EAV Fields
        """
        return []

    def getContent(self):
        return self.context.data

    @view.memoize
    def buildForm(self):
        fields = self.getPreFields()
        groups = self.getPreGroups()
        for name, field in self.context.formschema.items():
            #sorted(self.entry.schema.items(), key = lambda f: f[1].order):
            prefix = str(name)
            if field.type == 'object':
                fieldset = DataEntryGroup(self.context, self.request, self)
                fieldset.__name__ = str(name)
                fieldset.prefix = prefix
                fieldset.label = field.title
                fieldset.description = field.description
                for subname, subfield in sorted(field.object_schema.items(), key=lambda f: f[1].order):
                    fieldset.fields += z3c.form.field.Fields(IField(subfield), prefix=prefix)
                groups.append(fieldset)
            else:
                zField = z3c.form.field.Field(IField(field))
                fields += z3c.form.field.Fields(zField, prefix=prefix)
            groups.extend(self.getPostGroups())
        return(fields, groups)


class DataEntryForm(z3c.form.group.GroupForm, DataForm, z3c.form.form.Form):
    """
    A form for entering data into DataStore
    """
    implements(interfaces.IDataEntryForm)
    template = ViewPageTemplateFile('entry_templates/form.pt')

    @property
    def formState(self):
        return self.context.item.state

    def update(self):
        """
        Builds the z3c form out of the schema
        """
        self.request.set('disable_border', True)
        self.fields = z3c.form.field.Fields()
        self.groups = []
        if self.context.item.state != 'not-done':
            (self.fields, self.groups) = self.buildForm()
        super(DataEntryForm, self).update()

    @property
    def mode(self):
        if self.context.item.state == u'complete':
            return DISPLAY_MODE
        return INPUT_MODE

    def applyChanges(self, data):
        """
        """
        changes = []
        entity = self.context.item
        collect_date = data.pop('collect_date', date.today())
        if entity.collect_date != collect_date:
            entity.collect_date = collect_date
        for key, value in data.items():
            (sub1, sep, sub2) = key.partition('.')
            if sep:
                subobj = entity[sub1]
                if subobj is None:
                    subschema = entity.schema[sub1].object_schema
                    subname = "%s_%s" % (entity.name, sub1)
                    subobj = model.Entity(name=subname, title=subschema.title, schema=subschema, collect_date=collect_date)
                    self.context.session.add(subobj)
                    self.context.session.flush()
                    entity[sub1] = subobj
                    self.context.session.flush()
                if subobj[sub2] != value:
                    changes.append(key)
                    subobj[sub2] = value
                if subobj.collect_date != collect_date:
                    subobj.collect_date = collect_date
            else:
                if entity[sub1] != value:
                    changes.append(key)
                    entity[sub1] = value
            self.context.session.flush()
        return changes

    def can_save(self):
        return  self.formState in [u'pending-entry', u'pending-review']

    @z3c.form.button.buttonAndHandler(_('Save'), name='save', condition=lambda self: self.can_save())
    def save(self, action):
        """
        Form button hander.
        """
        data, errors = self.extractData()
        if errors:
            self.status = _(u"Please correct the highlighted errors.")
            return
        self.applyChanges(data)
        self.context.item.state = u'pending-review'
        self.context.session.flush()
        message = _(u"You have completed %s." % self.context.title)
        IStatusMessage(self.request).addStatusMessage(message, type="info")
        return self.request.response.redirect(self.context.aq_parent.absolute_url())

    @z3c.form.button.buttonAndHandler(_('Start Over'), name='restart', condition=lambda self: self.can_restart())
    def restart(self, action):
        """
        Restart the form by redirecting to the same page
        """
        self.request.response.redirect(self.action)

DataEntryFormView = plone.z3cform.layout.wrap_form(DataEntryForm)

class DataAddForm(z3c.form.group.GroupForm, DataForm, z3c.form.form.AddForm):
    """
    A form for entering data into DataStore
    """
    implements(interfaces.IDataEntryForm)
    template = ViewPageTemplateFile('entry_templates/form.pt')

    @property
    def formState(self):
        return 'pending-entry'

    def update(self):
        """
        Builds the z3c form out of the schema
        """
        self.request.set('disable_border', True)
        self.fields = z3c.form.field.Fields()
        self.groups = []
        (self.fields, self.groups) = self.buildForm()
        super(DataAddForm, self).update()

    def create(self, data):
        collect_date = data.pop('collect_date', date.today())
        formstate = data.pop('formstate', u'pending-review')
        formTitle = self.context.formschema.name + datetime.now().isoformat()
        newEntity = model.Entity(schema=self.context.formschema, name=formTitle, title=self.context.formschema.name, state=formstate, collect_date=collect_date)
        self.context.session.add(newEntity)
        self.context.session.flush()
        for key, value in data.items():
            (sub1, sep, sub2) = key.partition('.')
            if sep:
                subobj = newEntity[sub1]
                if subobj is None:
                    subschema = newEntity.schema[sub1].object_schema
                    subname = "%s_%s" % (newEntity.name, sub1)
                    subobj = model.Entity(name=subname, title=subschema.title, schema=subschema, collect_date=collect_date)
                    self.context.session.add(subobj)
                    self.context.session.flush()
                    newEntity[sub1] = subobj
                if subobj[sub2] != value:
                    subobj[sub2] = value
            else:
                if newEntity[sub1] != value:
                    newEntity[sub1] = value
            self.context.session.flush()
        return newEntity

    def add(self, object):
        context = self.context.closestModel()
        notify(EntityMovedEvent(context, object))
        modified(closest(self.context, interfaces.IClinicalObject))
        return object

    def nextURL(self):

        return self.context.getParentNode().absolute_url()

DataAddFormView = plone.z3cform.layout.wrap_form(DataAddForm)

class DataEntryAddForm(z3c.form.group.GroupForm, z3c.form.form.AddForm):
    """
    Form for adding data when creating Plone content
    """
    implements(interfaces.IDataEntryForm)
    z3c.form.form.extends(z3c.form.form.AddForm)

    label = _(u'Enter Forms')

    enable_form_tabbing = False
    entryForms = list()

    def getPreFields(self):
        """
        Fields that should appear before the EAV Fields
        """
        return z3c.form.field.Fields()

    def getPreGroups(self):
        """
        Group Fields that should appear before the EAV Fields
        """
        return []

    def getPostGroups(self):
        """
        Group Fields that should appear after the EAV Fields
        """
        return []

    def getContent(self):
        return dict()

    def getSchema(self, formName, Session):
        thisdate = getattr(self.context, 'visit_date', date.today())
        formQ = (
            Session.query(model.Schema)
            .filter(model.Schema.name == formName)
            .filter(model.Schema.state == 'published')
            .filter(model.Schema.publish_date < thisdate)
            .order_by(model.Schema.publish_date.desc())
            .limit(1)
            )
        try:
            form = formQ.one()
        except NoResultFound:
            form = None
        return form

    @view.memoize
    def getForms(self):
        fields = self.getPreFields()
        groups = self.getPreGroups()
        # Add the data entry forms
        for formName, connection in self.entryForms:
            Session = named_scoped_session(connection)
            schema = self.getSchema(formName, Session)
            if schema:
                for name, field in sorted(schema.items(), key=lambda f: f[1].order):
                    prefix = str('%s.%s') % (str(schema.name), str(name))
                    if field.type == 'object':
                        fieldset = DataEntryGroup(self.context, self.request, self)
                        fieldset.__name__ = prefix
                        fieldset.label = field.title
                        fieldset.description = field.description
                        for name, field in sorted(field.object_schema.items(), key=lambda f: f[1].order):
                            fieldset.fields += z3c.form.field.Fields(IField(field), prefix=prefix)
                        groups.append(fieldset)
                    else:
                        zField = z3c.form.field.Field(IField(field), name=prefix)
                        fields += z3c.form.field.Fields(zField, prefix=prefix)
        groups.extend(self.getPostGroups())
        return (fields, groups)

    def update(self):
        if not getattr(self, '_fields', None) or not getattr(self, '_groups', None):
            (self._fields, self._groups) = self.getForms()
        self.fields = self._fields
        self.groups = self._groups
        super(DataEntryAddForm, self).update()

    def extractEntries(self, data):
        # We're going to extract the incoming data to their appropriate
        # form entry data (properly nested, of course)
        entries = dict()

        # First do the fields
        for field in self.fields.values():
            (formName, dot, fieldName) = field.__name__.partition('.')
            if fieldName and field.__name__ in data:
                entries.setdefault(formName, dict())
                entries[formName].setdefault(fieldName, None)
                z3c.form.form.applyChanges(self, entries[formName], {field.__name__: data[field.__name__]})

        # Next extract the the groups
        for group in self.groups:
            (formName, dot, fieldName) = group.__name__.partition('.')
            if fieldName:
                entries.setdefault(formName, dict())
                entries[formName].setdefault(fieldName, dict())
                z3c.form.form.applyChanges(group, entries[formName][fieldName], data)

        return entries

    def addEntry(self, formschema, data, newEntity=None):
        Session = object_session(formschema)
        collect_date = data.pop('collect_date', date.today())
        formstate = data.pop('formstate', u'pending-review')
        formTitle = formschema.name + datetime.now().isoformat()
        if newEntity is None:
            newEntity = model.Entity(schema=formschema, name=formTitle, title=formschema.name, state=formstate, collect_date=collect_date)
            Session.add(newEntity)
            Session.flush()
        else:
            newEntity.state = formstate
            Session.flush()
        for key, val in data.items():
            if type(val) == dict:
                if newEntity[key] is None:
                    subschema = formschema[key].object_schema
                    subtitle = "%s%s" % (formTitle, subschema.name)
                    subEntity = model.Entity(schema=subschema, name=subtitle, title=subtitle, state=u'inline', collect_date=collect_date)
                    Session.add(subEntity)
                    Session.flush()
                    newEntity[key] = subEntity
                for subkey, subval in val.items():
                    newEntity[key][subkey] = subval
            else:
                newEntity[key] = val
        Session.flush()
        return newEntity


    def createAndAdd(self, data):
        """
        Add extra functionality to the base class's ``createAndAdd``.
        Note that the extending class must still implement the expected
        ``create``, ``add``, and ``nextURL`` methods expected by ``z3c.form``
        """

        entries = self.extractEntries(data)
        for formName, connection in self.entryForms:
            self.addEntry(formName, entries[formName])
        return None


    @z3c.form.button.buttonAndHandler(_('Start Over'), name='restart')
    def restart(self, action):
        self.request.response.redirect(self.action)



class DataEntryEditForm(z3c.form.group.GroupForm, z3c.form.form.EditForm):
    """
    Form for adding data when creating Plone content
    """
    implements(interfaces.IDataEntryForm)
    z3c.form.form.extends(z3c.form.form.EditForm)

    template = viewpagetemplatefile.ViewPageTemplateFile('entry_templates/uberform.pt')

    label = _(u'Enter Forms')

    enable_form_tabbing = False
    entryForms = list()

    def getPreFields(self):
        """
        Fields that should appear before the EAV Fields
        """
        return z3c.form.field.Fields()

    def getPreGroups(self):
        """
        Group Fields that should appear before the EAV Fields
        """
        return []

    def getPostGroups(self):
        """
        Group Fields that should appear after the EAV Fields
        """
        return []

    def getContent(self):
        return self.context.data

    def getSchema(self, formName, Session):
        thisdate = getattr(self.context, 'visit_date', date.today())
        formQ = (
            Session.query(model.Schema)
            .filter(model.Schema.name == formName)
            .filter(model.Schema.state == 'published')
            .filter(model.Schema.publish_date < thisdate)
            .order_by(model.Schema.publish_date.desc())
            .limit(1)
            )
        try:
            form = formQ.one()
        except NoResultFound:
            form = None
        return form

    def buildGroup(self, schema, label=None, description=None, prefix=None):
        groups = []
        if not prefix:
            prefix = str(schema.name)
        fieldset = DataEntryGroup(self.context, self.request, self)
        fieldset.__name__ = prefix
        fieldset.label = label and label or schema.title
        fieldset.description = description and description or schema.description
        fieldset.fields = z3c.form.field.Fields()
        for name, field in sorted(schema.items(), key=lambda f: f[1].order):
            subprefix = str('%s.%s') % (prefix, str(name))
            if field.type == 'object':
                groups.append(self.buildGroup(
                                            field.object_schema,
                                            label=field.title,
                                            description=field.description,
                                            prefix=subprefix))
            else:
                zField = z3c.form.field.Field(IField(field), name=subprefix)
                fieldset.fields += z3c.form.field.Fields(zField, prefix=subprefix)
        fieldset.groups = groups
        return fieldset

    @view.memoize
    def getForms(self):
        fields = self.getPreFields()
        groups = self.getPreGroups()
        # Add the data entry forms
        for formName, connection in self.entryForms:
            Session = named_scoped_session(connection)
            schema = self.getSchema(formName, Session)
            if schema:
                fieldset = self.buildGroup(schema)
                # fields +=subfields
                groups.append(fieldset)
        groups.extend(self.getPostGroups())
        return (fields, groups)

    def update(self):
        if not getattr(self, '_fields', None) or not getattr(self, '_groups', None):
            (self._fields, self._groups) = self.getForms()
        self.fields = self._fields
        self.groups = self._groups
        super(DataEntryEditForm, self).update()

    def extractEntries(self, data):
        # We're going to extract the incoming data to their appropriate
        # form entry data (properly nested, of course)
        entries = dict()

        # First do the fields
        for field in self.fields.values():
            (formName, dot, fieldName) = field.__name__.partition('.')
            if fieldName and field.__name__ in data:
                entries.setdefault(formName, dict())
                entries[formName].setdefault(fieldName, None)
                z3c.form.form.applyChanges(self, entries[formName], {field.__name__: data[field.__name__]})

        # Next extract the the groups
        for group in self.groups:
            (formName, dot, fieldName) = group.__name__.partition('.')
            if fieldName:
                entries.setdefault(formName, dict())
                entries[formName].setdefault(fieldName, dict())
                z3c.form.form.applyChanges(group, entries[formName][fieldName], data)

        return entries