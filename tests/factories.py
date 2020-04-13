"""
Automated fake data factories declarations

Auto-populates data structures with fake data for testing.
Note that dependent structures are only implemented minimally.

Do not import this module directly, we've setup a fixture for this.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from occams import models


class FakeDescribeable(factory.Factory):
    # It's really diffcult to generate a slug from a title in a random
    # test so just make a trully random name for the record
    name = factory.Faker('uuid4')
    title = factory.Faker('word')
    description = factory.Faker('paragraph')


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.User
    key = factory.Faker('email')


class ChoiceFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Choice
    name = factory.Sequence(lambda n: '{0:08d}'.format(n))
    title = factory.Faker('word')
    order = factory.Sequence(lambda n: n)


class AttributeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Attribute
    name = factory.Sequence(lambda n: 'var_{}'.format(n))
    title = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    type = 'string'
    order = factory.Sequence(lambda n: n)


class SchemaFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Schema
    name = factory.Sequence(lambda n: 'form_{}'.format(n))
    title = factory.Faker('word')
    description = factory.Faker('paragraph')
    publish_date = factory.Faker('date_time_this_year')


class EntityFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Entity
    schema = factory.SubFactory(SchemaFactory)


class StudyFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = models.Study
    short_title = factory.Faker('word')
    code = factory.Faker('credit_card_security_code')
    consent_date = factory.Faker('date_time_this_year')


class ExternalServiceFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = models.ExternalService

    url_template = factory.Faker('url')
    study = factory.SubFactory(StudyFactory)


class CycleFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = models.Cycle
    study = factory.SubFactory(StudyFactory)
    week = factory.Faker('pyint')


class ArmFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = models.Arm
    study = factory.SubFactory(StudyFactory)


class SiteFactory(SQLAlchemyModelFactory, FakeDescribeable):
    class Meta:
        model = models.Site
    title = factory.Faker('city')


class PatientFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Patient
    site = factory.SubFactory(SiteFactory)
    pid = factory.Faker('uuid4')


class ReferenceTypeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.ReferenceType


class PatientReference(SQLAlchemyModelFactory):
    class Meta:
        model = models.ReferenceType
    patient = factory.SubFactory(PatientFactory)
    reference_type = factory.SubFactory(ReferenceTypeFactory)
    reference_number = factory.Faker('uuid4')


class EnrollmentFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Enrollment
    patient = factory.SubFactory(PatientFactory)
    study = factory.SubFactory(StudyFactory)
    reference_number = factory.Faker('ean8')
    consent_date = factory.Faker('date_time_this_year')
    latest_consent_date = factory.LazyAttribute(lambda o: o.consent_date)


class StratumFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Stratum
    study = factory.SubFactory(StudyFactory)
    arm = factory.SubFactory(
        ArmFactory,
        study=factory.SelfAttribute('..study'))
    label = factory.Faker('word')
    block_number = factory.Faker('pyint')
    randid = factory.Faker('uuid4')


class VisitFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Visit
    patient = factory.SubFactory(PatientFactory)
    visit_date = factory.Faker('date_time_this_year')


class ExportFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Export
    name = factory.Faker('uuid4')
    owner_user = factory.SubFactory(UserFactory)
    expand_collections = False
    use_choice_labels = False
    status = 'pending'
    contents = {}
