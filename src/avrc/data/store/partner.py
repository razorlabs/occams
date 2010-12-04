""" Contains how to: domain and protocol
"""

import transaction
from zope.component import adapts
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from avrc.data.store._utils import DatastoreConventionalManager
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IPartner
from avrc.data.store.interfaces import IPartnerManager
from avrc.data.store import model


class Partner(object):
    """ See `IPartner`
    """
    implements(IPartner)

    zid = FieldProperty(IPartner["zid"])

    subject_zid = FieldProperty(IPartner["subject_zid"])

    enrolled_subject_zid = FieldProperty(IPartner["enrolled_subject_zid"])

    visit_zid = FieldProperty(IPartner["visit_zid"])


class DatastorePartnerManager(DatastoreConventionalManager):
    """ See `IPartnerManager`
    """
    adapts(IDatastore)
    implements(IPartnerManager)

    def __init__(self, datastore):
        super(DatastorePartnerManager, self).__init__(
            datastore=datastore,
            model=model.Partner,
            type=Partner
            )


    def putProperties(self, rslt, source):
        """ Add the items from the source to Datastore
        """
        rslt.zid = source.zid
        rslt.subject_zid = source.subject_zid
        rslt.enrolled_subject_zid = source.enrolled_subject_zid
        rslt.visit_zid = source.visit_zid


    def getEnteredDataOfType(self, partner, schema_name):
        """ Get all of the data entered for a visit
        """
        Session = self._datastore.getScopedSession()
        session = Session()

        instance_rslt = session.query(model.Instance)\
            .join(self._model.instances)\
            .filter(self._model.zid==partner.zid)\
            .join(model.Schema)\
            .join(model.Specification)\
            .filter_by(name=schema_name)\
            .first()

        if not instance_rslt:
            return None

        return self._datastore.get(instance_rslt.title)


    def add_instances(self, partner, obj_or_list):
        """ ??!? """
        Session = self._datastore.getScopedSession()
        session = Session()

        partner_rslt = session.query(self._model)\
            .filter_by(zid=partner.zid)\
            .first()

        for obj in obj_or_list:
            obj_rslt = session.query(model.Instance)\
                .filter_by(title=obj.title)\
                .first()

            partner_rslt.instances.append(obj_rslt)

        transaction.commit()
