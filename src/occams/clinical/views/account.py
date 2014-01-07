#import colander
#import deform.widget
#from pyramid.decorator import reify
#from pyramid.httpexceptions import HTTPFound
#from pyramid.security import remember, forget
#from pyramid.view import view_config, forbidden_view_config
#from pyramid_ldap import get_ldap_connector
#from sqlalchemy import orm
#import transaction

#from occams.clinical import _, log, permissions, Session
#from occams.datastore import model as datastore


#class LoginSchema(colander.MappingSchema):

    #email = colander.SchemaNode(
        #colander.String(),
        #title=None,
        #validator=colander.All(
            #colander.Email(),
            #colander.Length(max=32)),
        #widget=deform.widget.TextInputWidget(
            #autofocus=True,
            #placeholder=_(u'Email')))

    #password = colander.SchemaNode(
        #colander.String(),
        #title=None,
        #validator=colander.Length(min=5, max=32),
        #widget=deform.widget.PasswordWidget(
            #placeholder=_(u'Password')))

    #@colander.deferred
    #def validator(self, kw):
        #def callback(node, cstruct):
            #request = kw['request']
            #ldap = get_ldap_connector(request)
            #record = ldap.authenticate(cstruct['email'], cstruct['password'])
            #if record is None:
                #raise colander.Invalid(node, _(u'Invalid credentials'))
        #return callback


#@view_config(
    #route_name='account_login',
    #renderer='occams.clinical:templates/account/login.pt')
#@forbidden_view_config(
    #renderer='occams.clinical:templates/account/login.pt')
#def login(request):
    #request.layout_manager.layout.title = _('Log In')
    #request.layout_manager.layout.show_header = False

    ## Figure out where the user came from so we can redirect afterwards
    #referrer = request.GET.get('referrer', request.current_route_path())
    #if not referrer or referrer == request.route_path('account_login'):
        ## Never use the login as the referrer
        #referrer = request.route_path('clinical')

    #form = deform.Form(
        #schema=LoginSchema(title=_(u'Please log in')).bind(request=request),
        #css_class='form-login',
        #action=request.route_path(
            #'account_login',
            #_query={'referrer': referrer}),
        #buttons=[
            #deform.Button(
                #'submit',
                #title=_(u'Sign In'),
                #css_class='btn btn-lg btn-primary btn-block')])

    #if not request.POST:
        #return {'form': form.render()}

    #try:
        #appstruct = form.validate(request.POST.items())
    #except deform.ValidationFailure as e:
        #return {'form': e.field.render({'email': request.POST['email']})}

    #try:
        #Session.query(datastore.User).filter_by(key=appstruct['email']).one()
    #except orm.NoResultFound as e:
        #with transaction.manager:
            #Session.add(datastore.User(key=appstruct['email']))

    #connector = get_ldap_connector(request)
    #with connector.manager.connection() as conn:
        #search = connector.registry.ldap_login_query
        #dn, attrs = search.execute(conn, login=appstruct['email'])[0]
    #headers = remember(request, dn)
    #return HTTPFound(location=referrer, headers=headers)


#@view_config(route_name='account_logout')
#def logout(request):
    #headers = forget(request)
    #return HTTPFound(location=request.route_path('clinical'), headers=headers)
