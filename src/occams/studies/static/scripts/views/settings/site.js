function SiteManageView(sitesUrl){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isAjaxing = ko.observable(false);

  self.sites = ko.observableArray();

  self.hasSites = ko.pureComputed(function(){
    return self.sites().length > 0;
  });

  self.sortSites = function(){
    self.sites.sort(function(a, b){ return a.title().localeCompare(b.title()); });
  };

  self.errorMessage = ko.observable();

  var VIEW = 'view', EDIT = 'edit', DELETE = 'delete';

  self.selectedSite = ko.observable();
  self.editableSite = ko.observable();
  self.latestSite = ko.observable();
  self.addMoreSites = ko.observable(false);
  self.statusSite = ko.observable();
  self.showEditSite = ko.pureComputed(function(){ return self.statusSite() == EDIT; });
  self.showDeleteSite = ko.pureComputed(function(){ return self.statusSite() == DELETE; });

  self.clear = function(){
    self.selectedSite(null);
    self.editableSite(null);
    self.latestSite(null);
    self.addMoreSites(false);
    self.statusSite(null);
  };

  self.startAddSite = function(){
    self.startEditSite(new Site());
  }

  self.startEditSite = function(site){
    self.statusSite(EDIT)
    self.selectedSite(site);
    self.editableSite(new Site(ko.toJS(site)));
  };

  self.startDeleteSite = function(site){
    self.statusSite(DELETE)
    self.selectedSite(site);
  };

  self.saveSite = function(element){
    if ($(element).validate().form()){
      var selected = self.selectedSite(),
          isNew = !selected.id();
      $.ajax({
        url: isNew ? $(element).attr('action') : selected.__url__(),
        method: isNew ? 'POST' : 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableSite()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        errors: handleXHRError({form: element, logger: self.errroMessage}),
        beforeSend: function(){
          self.isAjaxing(true);
        },
        success: function(data){
          if (isNew){
            var site = new Site(data);
            self.sites.push(site);
            self.latestSite(site);
          } else {
            selected.update(data);
          }

          self.sortSites();

          if (self.addMoreSites()){
            self.startAddSite();
          } else {
            self.clear();
          }
        },
        complete: function(){
          self.isAjaxing(false);
        }
      });
    }
  };

  self.deleteSite = function(element){
    var selected = self.selectedSite();
    $.ajax({
      url: selected.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      errors: handleXHRError({form: element, logger: self.errroMessage}),
      beforeSend: function(){
        self.isAjaxing(true);
      },
      success: function(data){
        self.sites.remove(selected);
        self.clear();
      },
      complete: function(){
        self.isAjaxing(false);
      }
    });
  };

  $.get(sitesUrl, function(data){
    self.sites(data.sites.map(function(value){ return new Site(value); }));
    self.sortSites();
    self.isReady(true);
  });
}
