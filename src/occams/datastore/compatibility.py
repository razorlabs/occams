
from zope.interface.interface import InterfaceClass
from occams.datastore import directives
from occams.datastore import model


def schema2iface(session, schema):
    # Process the base classes first
    if schema.base_schema:
        ibase = schema2iface(schema.base_schema)
    else:
        ibase = directives.Schema

    iface = InterfaceClass(
        name=str(schema.name),
        bases=[ibase],
        attrs=[attribute2field(a) for a in schema.attributes],
        )

    directives.__id__.set(iface, schema.id)
    directives.title.set(iface, schema.title)
    directives.description.set(iface, schema.description)
    directives.version.set(iface, schema.create_date)

    return iface

def iface2schema(session, iface):
    if not directives.Schema.isEqualOrExtendedBy(iface):
        raise ValueError('%s is not a child class of %s' % (iface, directives.Schema))

    if 1 < len(iface.__bases__):
        raise MultipleBasesError
    elif 1 == len(iface.__bases__) and directives.Schema != iface.__bases__[0]:
        base_schema = iface2schema(session, iface.__bases__[0])
    else:
        base_schema = None

    schema = model.Schema(base_schema=base_schema, name=key)
    session.add(schema)

    schema.title = directives.title.bind().get(item)
    schema.description = directives.description.bind().get(item)
    if schema.description is not None:
        # Sanitize the description (i.e. make sure no empty strings)
        schema.description = schema.description.strip() or None
    session.flush()

    directives.__id__.set(item, schema.id)
    directives.version.set(item, schema.create_date)

    manager = FieldManager(schema)
    for order, field in enumerate(zope.schema.getFieldsInOrder(item), start=0):
        (name, field) = field
        field.order = order # sanitize the order
        manager.put(name, field)

    return schema.id

def attribute2field(session, attribute):
    factory = typesVocabulary.getTermByToken(attribute.type).value
    options = dict()

    if attribute.object_schema:
        manager = SchemaManager(session)
        schema = manager.get(attribute.object_schema.name, on=on)
        factory = zope.schema.Object
        options = dict(schema=schema)

    if attribute.choices:
        terms = []
        validator = factory(**options)
        query = (
            session.query(model.Choice)
            .filter_by(attribute=attribute)
            .order_by(model.Choice.order.asc())
            )

        for choice in query.all():
            (token, title, value) = (choice.name, choice.title, choice.value)
            term = SimpleTerm(token=str(token), title=title, value=value)
            terms.append(term)
        factory = zope.schema.Choice
        options = dict(vocabulary=SimpleVocabulary(terms))

    if attribute.is_collection:
        # Wrap the factory and options into the list
        options = dict(value_type=factory(**options), unique=True)
        factory = zope.schema.List

    if attribute.default:
        options['default'] = factory(**options).fromUnicode(attribute.default)
    # Update the options with the final field parameters
    options.update(dict(
        __name__=str(attribute.name),
        title=attribute.title,
        description=attribute.description,
        readonly=attribute.is_readonly,
        required=attribute.is_required,
        ))

    result = factory(**options)
    result.order = attribute.order

    if attribute.choices:
        directives.type.set(result, attribute.type)
    directives.__id__.set(result, attribute.id)
    directives.version.set(result, attribute.create_date)

    return result

def field2attribute(session, field):
    if self.schema.remove_date is not None:
        raise Exception('Cannot modify a schema field that has been retired.')
    session = self.session
    is_collection = zope.schema.interfaces.ICollection.providedBy(item)
    field = item if not is_collection else item.value_type
    choices = dict()
    object_schema = None

    self.retire(field.__name__)

    if zope.schema.interfaces.IChoice.providedBy(field):
        type = directives.type.bind().get(item)
        try:
            validator = (typesVocabulary.getTermByToken(type).value)()
        except LookupError:
            raise ChoiceTypeNotSpecifiedError

        for i, term in enumerate(field.vocabulary, start=0):
            (name, title, value) = (term.token, term.title, term.value)
            validator.validate(value)
            title = title is None and name or title
            title = unicode(title)
            name = str(name)
            value = unicode(value)
            choice = model.Choice(name=name, title=title, value=value, order=i)
            choices[choice.name] = choice
    else:
        try:
            type = typesVocabulary.getTerm(field.__class__).token
        except LookupError:
            raise TypeNotSupportedError

        if zope.schema.interfaces.IObject.providedBy(field):
            iface = field.schema
            object_schema_id = directives.__id__.bind().get(iface)
            object_schema = session.query(model.Schema).get(object_schema_id)

    attribute = model.Attribute(
        schema=self.schema,
        name=item.__name__,
        title=item.title,
        description=item.description,
        type=type,
        choices=choices,
        object_schema=object_schema,
        is_inline_object=directives.inline.bind().get(field),
        is_readonly=item.readonly,
        is_collection=is_collection,
        is_required=item.required,
        default=(unicode(item.default) if item.default is not None else None),
        order=item.order
        )

    if attribute.description is not None:
        attribute.description = attribute.description.strip() or None

    session.add(attribute)
    session.flush()

    directives.__id__.set(item, attribute.id)
    directives.version.set(item, attribute.create_date)

    return attribute.id

def entity2data(session, entity):
    manager = ValueManager(entity)
    values = dict([(n, manager.get(n, on=on)) for n in manager.keys(on=on)])
    iface = SchemaManager(session).get(entity.schema.name, on=entity.collect_date)
    result = ObjectFactory(iface, **values)
    result.__dict__.update(dict(
        __id__=entity.id,
        __name__=entity.name,
        __title__=entity.title,
        __schema__=iface,
        __state__=(entity.state and entity.state.name or None),
        __version__=entity.create_date,
        ))
    return entity

def data2entity(session, data):
    def put(self, key, item):
        if not IInstance.providedBy(item):
            raise InvalidObjectError

        session = self.session
        name = u''
        title = u''
        is_new = True
        iface = item.__schema__

        state = item.getState()
        filter = state is None and dict(is_default=True) or dict(name=state)
        state = session.query(model.State).filter_by(**filter).first()

        if item.__name__ is not None:
            name = item.__name__
            title = item.__title__
            is_new = False
            self.retire(name)

        entity = model.Entity(
            schema_id=directives.__id__.bind().get(iface),
            name=name,
            title=title,
            state=state,
            )
        session.add(entity)
        session.flush()

        if is_new:
            schema_title = directives.title.bind().get(iface)
            entity.name = '%s-%d' % (iface.__name__, entity.id)
            entity.title = u'%s-%d' % (schema_title, entity.id)
            session.flush()

        item.__id__ = entity.id
        item.__name__ = entity.name
        item.__title__ = entity.title
        item.__schema__ = iface
        item.__state__ = entity.state and entity.state.name or None
        item.__version__ = entity.create_date
        item.__collect_date__ = entity.collect_date

        value_manager = ValueManager(entity)

        for field_name, field in zope.schema.getFieldsInOrder(iface):
            value = getattr(item, field_name, None)
            value_manager.put(field_name, value)

        return item.__id__

def raw2value(session, raw):
        session = self.session
        item = item if isinstance(item, list) else [item]
        result = None
        entries = []
        entity = self.entity

        if entity.remove_date is not None:
            raise Exception('Cannot modify an entity that has already been retired.')

        if isinstance(key, basestring):
            query = (
                session.query(model.Attribute)
                .filter_by(name=key, schema=entity.schema)
                .filter(model.Attribute.asOf(None))
                )
            attribute = query.first()
        else:
            attribute_id = directives.__id__.bind().get(key)
            attribute = entity.schema.attributes.get(attribute_id)

        if attribute is None:
            raise PropertyNotDefinedError

        value_dsmodel = nameModelMap[attribute.type]

        query = (
            session.query(value_dsmodel)
            .filter_by(entity=entity, attribute=attribute, remove_date=None)
            )

        # RETIRE values not in the item and ignore existing values
        for entry in query.all():
            if item:
                if entry.value not in item:
                    entry.remove_date = model.NOW
                else:
                    item.remove(entry.value)

        for value in item:
            if value is not None:
                # Find the choice it came from before the value is converted
                query = (
                    session.query(model.Choice)
                    .filter_by(attribute=attribute, value=unicode(value))
                    )
                choice = query.first()
                if 'object' == attribute.type:
                    entity_manager = EntityManager(session)
                    value = entity_manager.put(getattr(value, '__name__', None), value)
                elif 'boolean' == attribute.type:
                    value = int(value)
                entry = value_dsmodel(
                    entity=entity,
                    attribute=attribute,
                    choice=choice,
                    value=value
                    )
                entries.append(entry)

        if entries:
            session.add_all(entries)
            session.flush()
            result = [entry.id for entry in entries]
            if not attribute.is_collection and len(result):
                result = result[0]

        return result
