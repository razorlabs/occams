from occams.form.form import Form
from occams.form.form import Group
import z3c.form.button
import os.path
from z3c.saconfig import named_scoped_session
from zope.security import checkPermission
from AccessControl import getSecurityManager

from occams.datastore import model
from occams.datastore.schema import copy

from occams.form import MessageFactory as _
from occams.form.interfaces import IRepository
from occams.form.traversal import closest

class DisabledMixin(object):
    """
    Disables all widgets in the form
    """

    def updateWidgets(self):
        super(DisabledMixin, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FormPreviewForm(DisabledMixin, Form):
    """
    Renders the form as it would appear during data entry
    """

    @property
    def label(self):
        formlabel = str(self.context.item.title) + ' -- '
        if self.context.item.publish_date:
            formlabel = formlabel + 'Published ' + self.context.item.publish_date.isoformat()
        else:
            formlabel = formlabel + 'Draft created by %(user_name)s on %(create_date)s' % dict(
                user_name=str(self.context.item.create_user.key),
                create_date=str(self.context.item.create_date.date().isoformat())
                )
        return formlabel

    @property
    def description(self):
        return self.context.item.description

    class PreviewGroup(DisabledMixin, Group):
        """
        Renders group in preview-mode
        """

    groupFactory = PreviewGroup

    @z3c.form.button.buttonAndHandler(_(u'<< Back to Listing'), name='cancel')
    def handleCancel(self, action):
        repository = closest(self.context, IRepository)
        self.request.response.redirect(repository.absolute_url())

    def can_edit(self):
        return (self.context.item.create_user.key == getSecurityManager().getUser().getId()) and \
        (not self.context.item.publish_date) and  \
        checkPermission("occams.form.ModifyForm", self.context) 

    @z3c.form.button.buttonAndHandler(_(u'Edit'), name='edit', condition= lambda self: self.can_edit())
    def handleEdit(self, action):
        self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@edit'))

    def can_draft(self):
        return checkPermission("occams.form.ModifyForm", self.context) 

    @z3c.form.button.buttonAndHandler(_(u'Draft New Version'), name='draft', condition= lambda self: self.can_draft())
    def handleDraft(self, action):
        Session = named_scoped_session(self.context.session)
        old_schema = Session.query(model.Schema).filter(model.Schema.id == self.context.item.id).one()
        new_schema = copy(old_schema)
        Session.add(new_schema)
        Session.flush()
        repositoryContext = closest(self.context, IRepository)
        self.request.response.redirect(os.path.join(repositoryContext.absolute_url(), str(new_schema.id), '@@edit'))

