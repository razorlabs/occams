#!/usr/bin/env python
"""Upgrade process for EAV versioning cleanup.

#########1#########2#########3#########4#########5#########6#########7#####

Design Assumptions:
    1. Reflect avrc_demo_data w/ sqlsoup (readonly to ensure no changes).
    2. No modifications to support tables (specimen, subject, etc) will be necessary.
    3. Remove dates will respect chronology (ie data processed in order leaves 
        final row with NULL remove date, and the rest "clean").
    4. The process will run in one go, within a single night or weekend.

Precondition Assumptions:
    1. There are two databases per run (eg avrc_demo_data and avrc_data)
    2. The avrc_data will start as a straight up copy of avrc_demo_data.
    3. For avrc_data we have "DROP TABLE"-ed: entity, state, datetime, 
        integer, object, decimal, string, schema, attribute, and choice.
    4. During the upgrade process, the website will be turned off.
    5. The source schema table is unique on (schema.name,DATE(create_date))
    6. We have run some SQL against gibbon that fixed some oddities in the source

-- choice fixing sql!!
-- run this to vierfy that gibbon has the same IDs as were problematic on gibbon-test-db
SELECT sc.name, sc.create_date, a.name, a.id, a.create_date
  FROM schema sc
    JOIN attribute a ON a.schema_id = sc.id
  WHERE sc.name IN ('FollowupHistoryNeedleSharingPartners','IEarlyTestMSMPartners')
;
-- run this to fix:
UPDATE attribute
  SET "create_date" = sc.create_date
  FROM schema sc
  WHERE sc.id = attribute.schema_id
    AND attribute.id IN (271,272,274,308,309,310,311,273)
;

-- Verify that two RapidTests are confused because of a create_date
-- on the *morning* before the RapidTest was versioned later that day
SELECT *
  FROM entity e
  WHERE DATE(e.create_date) = '2012-03-01'
    AND e.create_date < '2012-03-01 13:13:45.198454'
    AND e.schema_id IN (19,75)
;
-- Make the updated RapidTest always point to the new schema, an hour after it was created
UPDATE entity
  SET create_date = '2012-03-01 14:14:00.600112', schema_id = 75
  WHERE name IN ('RapidTest-148743')
    AND create_date = '2012-03-01 08:14:00.600112'
;
-- Make the RapidTest created that morning think it was created before the confusion started
UPDATE entity
  SET create_date = '2012-02-29 07:15:31.972552'
  WHERE name = 'RapidTest-148740'
    AND create_date = '2012-03-01 07:15:31.972552'
;

"""
from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from occams.datastore import model

from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import aliased

global Session
Session = scoped_session(
    sessionmaker(
        class_=model.DataStoreSession,
        user=(lambda : "bitcore@ucsd.edu") # can be called by a library
        ))

global old_model

global entity_state # Filled during Session creation and so on

def main():
    """Handle argv, specialize globals, launch job."""
    import sys
    usage = """overhaul.py OLDCONNECT NEWCONNECT"""
    configureGlobalSession(sys.argv[1], sys.argv[2])
    addUser("bitcore@ucsd.edu")
    entityLimit = 100
    print "Moving in all schemas and %s entities" % entityLimit
    moveInAllSchemas()
    moveInAttributesAndChoices()
    moveInEntities(limit=entityLimit)
#    moveInExternalContext()
    Session.commit()
    if isWorking():
        print "Yay!"

#def moveInExternalContext():
#    """Make up contents of "external", then fill "context" using intance tables."""
#    # SUBJECT LOGIC IS THE SIMPLEST
#    ext_subject = mode.External(
#        name="subject", title="anything?",
#        description="subject table in clinical DB")
#    Session.add(ext_subject)
#    Session.flush()
#    for our,parentEntityName in subjectInstances():
#        new_context = {
#            "entity_id":getNewEntityId(parentEntityName),
#            "external_id":ext_subject.id,
#            "key":our,
#            }
#        Session.add(model.Context(**new_context))
#    Session.flush()
#
#    # Then do the same basic thing (with increasing cleverness) for 
#    # the visit, partner, and enrollment instance tables...

def subjectInstances():
    """In the home stretch!"""
    our, parentEntityName = None,None
    yield our, parentEntityName

def moveInEntities(limit=None):
    """This function will probably work in stages to move entities.
    
    WORKING - Stage 1: Parent entities
    TO TEST - Stage 2: Child entities
    TO TEST - Stage 3: linking object values
    """
    counter = 0
    for name in yieldDistinctParentEntityNames():
        counter += 1
        if limit is not None and counter > limit:
            return
        # FIRST HANDLE THE PARENT ENTITIES
        newParentEntity = None
        newSchema = None
        the_create_date = None
        for sourceEntity,schema_name in yieldOrderedEntities(name):
            if newSchema is None:
                the_create_date = sourceEntity.create_date
                newSchema = getSchemaForEntity(schema_name,the_create_date)
            # Set up *this revision* for this parent
            newParentEntity = createEntity(sourceEntity,newParentEntity,newSchema)
            Session.add(newParentEntity)
            Session.flush()
            newParentEntity = updateValues(newParentEntity,sourceEntity)
            Session.flush()

            ## This section is commented out until Marco's datastore code to
            ## handle child attachment works...
           # 
           # # Use datastore's built in awesomeness to handle subentities and the
           # # implicit linking object values for this revision.  Then commit :)
           # for oldChildEntity,oldParentAttrName in yieldChildEntities(sourceEntity):
           #     newChildSchema = newSchema[oldParentAttrName].object_schema
           #     tempChildEntity = createEntity(
           #         oldChildEntity, 
           #         getattr(newParentEntity,oldParentAttrName,None),
           #         newChildSchema)
           #     newParentEntity[oldParentAttrName] = tempChildEntity
           #     #import pdb; pdb.set_trace()
           #     Session.flush()
           #     newParentEntity[oldParentAttrName] = updateValues(
           #         newParentEntity[oldParentAttrName],
           #         oldChildEntity)
           #     Session.flush()

def updateValues(partialNewEntity,oldEntity):
    """Return the same partialNewEntity, except augmented with old values."""
    for attribute in partialNewEntity.schema.values():
        if attribute.type == 'object': 
            # is_collection restriction is only here so we can test: non-collections first
            continue
        value = getOldValue(attribute, oldEntity)
        partialNewEntity[attribute.name] = value
    return partialNewEntity

def getOldValue(attribute, oldEntity):
    """Uses knowledge of attribute to return one of the entities old values."""
    type_to_table = {
        "boolean":"integer",
        "integer":"integer",
        "text":"string",
        "string":"string",
        "date":"datetime",
        "decimal":"decimal",
        }
    att = old_model.entity("attribute")
    val = old_model.entity(type_to_table[attribute.type])
    qry = (
        Session.query(val.value)
        .join(att, (att.id == val.attribute_id))
        .filter(att.name == attribute.name)
        .filter(val.entity_id == oldEntity.id)
        )
    if qry.count() > 1 and not attribute.is_collection:
        raise Exception("fml")
    elif attribute.is_collection:
        return qry.all()
    return qry.first()

def yieldChildEntities(oldParentEntity):
    """Get child entites with parrent attr names given parent entity name.
    
    For a given parent entity name, *skip* any non-object attributes it
    has... the whole point here is to handle parent/child linking issues,
    and the real meat of the forms (ints, dates, strings, etc) won't be
    handled till this skeleton exists."""
    from sqlalchemy.orm import aliased
    c_ent = aliased(old_model.entity("entity"))
    p_ent = old_model.entity("entity")
    obj = old_model.entity("object")
    att = old_model.entity("attribute")
    qry = (
        Session.query(c_ent, att.name) 
        .join(obj, (c_ent.id == obj.value))
        .join(p_ent, (p_ent.id == obj.entity_id))
        .filter(p_ent.id == oldParentEntity.id)
        .join(att, (att.id == obj.attribute_id)) 
        )
    return iter(qry)

def getSchemaForEntity(schema_name,entity_date):
    """Not plural == singular, not impossible publish version."""
    qry = (
        Session.query(model.Schema)
        .filter(model.Schema.name == schema_name)
        .filter(model.Schema.publish_date <= entity_date)
        .order_by(model.Schema.publish_date.desc())
        .limit(1)
        )
    return qry.one()

def moveInAttributesAndChoices():
    schemaChanges = getInstalledSchemas()
    for newSchema in schemaChanges:
        attrsAndChoices = getOriginalAttrsAndChoices(newSchema)
        createAttrsAndChoices(newSchema,attrsAndChoices)

def moveInAllSchemas():
    schemaChanges = getKnownSchemaChanges()
    for revision in schemaChanges:
        installed = 0
        #print "==========\nWorking on revision:",revision
        # PARENTS SCHEMAS
        p_original = getOriginalParentSchema(revision)
        new_parent = createSchema(revision,p_original)
        installed += 1
        # CHILD SCHEMAS AND THEIR LINKING PARENT ATTRIBUTES
        c_originals = getOriginalChildSchemas(p_original)
        for c_original in c_originals:
            new_child = createSchema(revision,c_original)
            installed += 1
            p_attr = getLinkingAttr(c_original)
            createLinkingAttr(revision,new_parent,new_child,p_attr)
        #print "Installed %s total schemas and related attributes." % installed

def createEntity(sourceEntity,prevNewEntity,newSchema):
    """Either create ur update (depending on prevNewEntity == None).
    
    This needs a Session.add(createEntity()) and a Session.flush().
    Those are your job as the user of this function."""
    global entity_state
    if prevNewEntity is None:
        prevNewEntity = model.Entity(
                create_date=sourceEntity.create_date,
                name=sourceEntity.name,
                schema=newSchema,
                )
    simples = ["name","title","description",]
    for simple in simples:
        setattr(prevNewEntity,simple,getattr(sourceEntity,simple))
    try:
        prevNewEntity.state = entity_state[sourceEntity.state_id]
    except KeyError as err:
        if "None" in err.__str__():
            prevNewEntity.state = "error"
        else:
            raise err
    prevNewEntity.modify_date = sourceEntity.create_date
    return prevNewEntity

def createAttrsAndChoices(newSchema,attrsAndChoices):
    """Given a schema name and revision date, create such a schema"""
    simpleAttr = [
            "name","title","description",
            "type","is_collection","is_required",
            "create_date","modify_date"
            ]
    simpleChoice = [
            "name","title","description","value",
            "create_date","modify_date"
            ]
    for i, (attribute, choices) in enumerate(attrsAndChoices):
        buildAttr = {
            "order":i,
            }
        for simple in simpleAttr:
            buildAttr[simple] = getattr(attribute,simple)
        newSchema[attribute.name] = model.Attribute(**buildAttr)
        for j, choice in enumerate(choices):
            buildChoice = {
                "order":j,
                }
            for simple in simpleChoice:
                buildChoice[simple] = getattr(choice,simple)
            newSchema[attribute.name].choices.append(model.Choice(**buildChoice))
    Session.flush()

def createSchema(revision,original):
    """Given a schema name and revision date, create such a schema"""
    form_name, publish_date = revision[0],revision[1]
    simples = ["name","title","description","storage","create_date","modify_date"]
    buildIt = {
        "state":"published",
        "publish_date":publish_date,
        }
    for simple in simples:
        buildIt[simple] = getattr(original,simple)
    toEnter = model.Schema(**buildIt)
    Session.add(toEnter)
    Session.flush()
    return toEnter


def getInstalledSchemas():
    """So simple it hurts :)"""
    return Session.query(model.Schema).order_by("publish_date").all()

def createLinkingAttr(revision,new_parent,new_child,p_attr):
     """Create the linking attributes between new parent and child attributes"""
     form_name, publish_date = revision[0],revision[1]
     simples = [
             "name","title","description",
             "type","is_collection","is_required","order",
             "create_date","modify_date"]
     buildIt = {
         # the "_id" will be added to the keys and the ".id" on the
         # instances will be handled by convention-respecting machinery
         # in model.Attribute when (**builtIt) is processed.
         "schema":new_parent,
         "object_schema":new_child,
         }
     for simple in simples:
         buildIt[simple] = getattr(p_attr,simple)
     toEnter = model.Attribute(**buildIt)
     Session.add(toEnter)
     Session.flush()

def yieldOrderedEntities(name):
    """Given entity name, yield entities themselves."""
    ent = old_model.entity("entity")
    sch = old_model.entity("schema")
    qry = (
        Session.query(ent,sch.name)
        .join(sch, (sch.id == ent.schema_id))
        .filter(ent.name == name)
        .order_by(
            ent.create_date,
            ent.remove_date.nullslast(),
            ent.id)
        )
    return iter(qry)

def yieldDistinctParentEntityNames():
    """Returns entity names that are *parent* entities only.
    
    Finding parents by left join where obj.value is NULL turns up
    274 "orphan child entities" that cause the code to crash.  These
    should be handled by some kind of separate cleaning process.
    When one is found it should be added to the assumptions at the
    top of this script.

    As a fallback, parent entities in this method are defined by 
    using a schema that isn't treated as a child schema in any 
    attribute."""
    ent = old_model.entity("entity")
    att = old_model.entity("attribute")
    qry = (
        Session.query(ent.name)
        .outerjoin(att, (ent.schema_id == att.object_schema_id))
        .filter(att.id == None)
        .group_by(ent.name)
        )
    for (item,) in qry:
        yield item

def getOriginalAttrsAndChoices(newSchema):
    """Taking new schema and finding the old attributes and choices for it
    
    Safe to use nothing but name and publish_date to connect things.
    Exclude the linking attributes that have already been set up.
    Choices are deep copied off of attributes so they're trivial to grab."""
    sch = old_model.entity("schema")
    att = old_model.entity("attribute")
    chc = old_model.entity("choice")
    publish_date = newSchema.publish_date
    qry = ( # All the attributes we want!
        Session.query(att)
        .join(sch,(sch.id == att.schema_id))
        .filter(sch.name == newSchema.name)
        .filter(cast(att.create_date,Date) <= publish_date)
        .filter((cast(att.remove_date,Date) > publish_date) | (att.remove_date == None))
        .filter(att.type != "object")
        .order_by(att.order.asc())
        )
    attributes = qry.all()
    out = []
    for attribute in attributes:
        qry = ( # Choices are deep copied and not complicated :)
            Session.query(chc)
            .filter(chc.attribute_id == attribute.id)
            .order_by(chc.order.asc())
            )
        choices = qry.all()
        out.append([attribute,choices])
    return out

def getLinkingAttr(c_original):
    """Get original parent attribute given original child schema"""
    sch = old_model.entity("schema")
    att = old_model.entity("attribute")
    qry = (
        Session.query(att)
        .filter(att.object_schema_id == c_original.id)
        )
    return qry.one()

def getOriginalChildSchemas(parent_schema):
    """Return all "original" child schemas for a given parent."""
    # NOTE: We know that child schemas were never really versioned
    # at the schema level.  Weird attributes, but that's it.
    sch = old_model.entity("schema")
    att = old_model.entity("attribute")
    qry = (
        Session.query(sch)
        .join(att,(sch.id == att.object_schema_id))
        .filter(att.schema_id == parent_schema.id)
        )
    return qry.all()

def getOriginalParentSchema(revision):
    """Return... Track down the template Yay!"""
    import sqlalchemy.exc
    form_name, publish_date = revision[0],revision[1]
    sch = old_model.entity("schema")
    qry = (
        Session.query(sch)
        .filter(sch.name == form_name)
        .filter(cast(sch.create_date,Date) <= publish_date)
        .filter((cast(sch.remove_date,Date) > publish_date) | (sch.remove_date == None))
        )
    try:
        out = qry.one()
    except sqlalchemy.exc.SQLAlchemyError as err:
        import pdb;pdb.set_trace()
        print "foo"
    return out

def addUser(email):
    #user = Session.query(model.User).filter(model.User.key == email).first()
    #if not user:
    Session.add(model.User(key=email))
    Session.flush()

def getKnownSchemaChanges(): 
    from sqlalchemy import func
    global Session
    changes = changeTableFactory(Session)
    subforms = subSchemaNamesTableFactory(Session)
    evilforms = baseSchemaNamesTableFactory(Session)
    realChanges = (
        Session.query(changes.c.schema_name, changes.c.change_date,func.count().label('revisionCount'))
        .filter(changes.c.change_date != None)
        .filter(~changes.c.schema_name.in_(subforms))
        .filter(~changes.c.schema_name.in_(evilforms))
        .group_by(changes.c.schema_name, changes.c.change_date)
        .order_by(changes.c.schema_name, changes.c.change_date)
        )
    return realChanges.all()

def configureGlobalSession(old_connect, new_connect):
    """Set up Session for data manipulation and create new tables as side effect."""
    global old_model
    global entity_state
    new_engine = create_engine(new_connect)
    model.Model.metadata.drop_all(bind=new_engine, checkfirst=True)
    model.Model.metadata.create_all(bind=new_engine, checkfirst=True)
    tables = []
    tables_model = model.Model.metadata.sorted_tables
    tables += dict.fromkeys(tables_model, new_engine).items()
    Session.configure(binds=dict(tables))
    old_model = SqlSoup(old_connect,session=Session)
    entity_state = getEntityStateDict()

def getEntityStateDict():
    """Returns entity state dictionary for use elsewhere."""
    state = old_model.entity("state")
    qry = (
        Session.query(state)
        )
    entity_state = {}
    for state in qry:
        entity_state[state.id] = state.name
    return entity_state

def baseSchemaNamesTableFactory(session):
    """Helper method to generate a SQLAlchemy expression table for base schemata names"""
    BaseSchema = aliased(old_model.entity("schema"), name='_base')
    # A query that builds a base schema name result set
    query = (
        session.query(BaseSchema.name)
        .join((old_model.entity("schema"), (old_model.entity("schema").base_schema_id == BaseSchema.id)))
        .group_by(BaseSchema.name)
        )
    return query.subquery()

def literal(value):
    """Helper method to convert a Python value into a SQL string"""
    return literal_column('\'%s\'' % str(value), String)

def subSchemaNamesTableFactory(session):
    """Helper method to generate a SQLAlchemy expression table for sub schemata names"""
    query = (
        session.query(old_model.entity("schema").name)
        .join((old_model.entity("attribute"), (old_model.entity("attribute").object_schema_id == old_model.entity("schema").id)))
        .group_by(old_model.entity("schema").name)
        )
    return query.subquery()

def changeTableFactory(session):
    """Helper method to generate a SQLAlchemy expression table for schemata changes.
    The result set will include all modifications done to each schema."""
    SubSchema = aliased(old_model.entity("schema"), name='_subschema')
    SubAttribute = aliased(old_model.entity("attribute"), name='_subattribute')

    # A query that builds a revision log result set of all master forms,
    # which also include the revisions of subforms
    query = (
        # Master schema create dates
        session.query(
            old_model.entity("schema").name.label('schema_name'),
            null().label('attribute_name'),
            cast(old_model.entity("schema").create_date,Date).label("change_date"),
            )
        .union(
            # Master schema removal dates
            session.query(
                old_model.entity("schema").name, 
                null(), 
                cast(old_model.entity("schema").remove_date,Date),
                ),
            # Master schema attribute create dates
            session.query(
                old_model.entity("schema").name,
                # Only report non-object values as part of the field count
                case([
                    (old_model.entity("attribute").type != literal('object'),
                        (old_model.entity("schema").name + literal('.') + old_model.entity("attribute").name))
                    ]),
                cast(old_model.entity("attribute").create_date,Date)
                )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id))),

            # Master schema attribute removal dates
            session.query(
                old_model.entity("schema").name, 
                null(), 
                cast(old_model.entity("attribute").remove_date,Date)
                )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id))),

            # Sub schema create dates
            session.query(
                old_model.entity("schema").name, 
                null(),
                cast(SubSchema.create_date,Date)
                )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id)))
            .join((SubSchema, (SubSchema.id == old_model.entity("attribute").object_schema_id))),

            # Sub schema removal dates
            session.query(
                old_model.entity("schema").name, 
                null(), 
                cast(SubSchema.remove_date,Date)
                )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id)))
            .join((SubSchema, (SubSchema.id == old_model.entity("attribute").object_schema_id))),

            # Sub schema attribute create dates
            session.query(
                old_model.entity("schema").name,
                SubSchema.name + literal('.') + SubAttribute.name,
                cast(SubAttribute.create_date,Date)
                )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id)))
            .join((SubSchema, (SubSchema.id == old_model.entity("attribute").object_schema_id)))
            .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id))),

            # Sub schema attribute removal dates
            session.query(
                    old_model.entity("schema").name, 
                    null(), 
                    cast(SubAttribute.remove_date,Date)
                    )
            .join((old_model.entity("attribute"), (old_model.entity("attribute").schema_id == old_model.entity("schema").id)))
            .join((SubSchema, (SubSchema.id == old_model.entity("attribute").object_schema_id)))
            .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id))),
            )
        )
    return query.subquery('_change')

def isWorking():
    """Did [] work?"""
    global old_model
    good = True
    #if Session.query(old_model.entity("schema")).count() != 32:
    #    print "Wrong number of schemas added"
    #    good = False
    return good

if __name__ == '__main__':
    main()

