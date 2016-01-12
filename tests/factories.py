"""
Automated fake data factories declarations

Auto-populates data structures with fake data for testing.
Note that dependent structures are only implemented minimally.

Do not import this module directly, we've setup a fixture for this.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from occams_datastore import models as datastore
from occams_studies import models as studies


class FakeDescribeable(factory.Factory):
    # It's really diffcult to generate a slug from a title in a random
    # test so just make a trully random name for the record
    name = factory.Faker('uuid4')
    title = factory.Faker('word')
    description = factory.Faker('paragraph')


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.User
    key = factory.Faker('email')


class ChoiceFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.Choice
    name = factory.Sequence(lambda n: '{0:08d}'.format(n))
    title = factory.Faker('word')
    order = factory.Sequence(lambda n: n)


class AttributeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.Attribute
    name = factory.Sequence(lambda n: 'var_{}'.format(n))
    title = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    type = 'string'
    order = factory.Sequence(lambda n: n)


class SchemaFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.Schema
    name = factory.Sequence(lambda n: 'form_{}'.format(n))
    title = factory.Faker('word')
    description = factory.Faker('paragraph')
    publish_date = factory.Faker('date_time_this_year')


class EntityFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.Entity
    schema = factory.SubFactory(SchemaFactory)


class StudyFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = studies.Study
    short_title = factory.Faker('word')
    code = factory.Faker('credit_card_security_code')
    consent_date = factory.Faker('date_time_this_year')


class CycleFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = studies.Cycle
    study = factory.SubFactory(StudyFactory)
    week = factory.Faker('pyint')


class ArmFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = studies.Arm
    study = factory.SubFactory(StudyFactory)


class SiteFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = studies.Site
    title = factory.Faker('city')


class PatientFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Patient
    site = factory.SubFactory(SiteFactory)
    pid = factory.Faker('uuid4')


class ReferenceTypeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.ReferenceType


class PatientReference(SQLAlchemyModelFactory):
    class Meta:
        model = studies.ReferenceType
    patient = factory.SubFactory(PatientFactory)
    reference_type = factory.SubFactory(ReferenceTypeFactory)
    reference_number = factory.Faker('uuid4')


class EnrollmentFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Enrollment
    patient = factory.SubFactory(PatientFactory)
    study = factory.SubFactory(StudyFactory)
    reference_number = factory.Faker('ean8')
    consent_date = factory.Faker('date_time_this_year')
    latest_consent_date = factory.LazyAttribute(lambda o: o.consent_date)


class StratumFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Stratum
    study = factory.SubFactory(StudyFactory)
    arm = factory.SubFactory(ArmFactory)
    label = factory.Faker('word')
    block_number = factory.Faker('pyint')
    randid = factory.Faker('uuid4')


class VisitFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Visit
    patient = factory.SubFactory(PatientFactory)
    visit_date = factory.Faker('date_time_this_year')


class ExportFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Export
    name = factory.Faker('uuid4')
    owner_user = factory.SubFactory(UserFactory)
    expand_collections = False
    use_choice_labels = False
    status = 'pending'
    contents = {}
