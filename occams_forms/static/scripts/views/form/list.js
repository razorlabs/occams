/**
 * Manages form listing
 */
function FormListView() {
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);          // Flag unhide body
  self.isSaving = ko.observable(false);
  self.isUploading = ko.observable(false);

  self.errorMessage = ko.observable();

  self.forms = ko.observableArray([]);          // Master list of forms
  self.filter = ko.observable();                // Filter string (i.e. search)

  self.hasForms = ko.pureComputed(function(){
    return self.forms().length > 0;
  });

  self.totalShowing  = ko.pureComputed(function(){
    return self.filteredForms().length;
  });

  self.totalForms = ko.pureComputed(function(){
    return self.forms().length;
  });

  self.lastUpdatedForm = ko.observable();       // Keep track of last updated form
  self.selectedForm = ko.observable();          // Current form in modal
  self.selectedFormErrors = ko.observable();
  self.showEditor = ko.observable(false);

  /**
   *  Filtered forms based on filter string>
   */
  self.filteredForms = ko.pureComputed(function(){
    var filter = self.filter();

    // No filter, return master list
    if (!filter) {
      return self.forms();
    }

    filter = filter.toLowerCase();

    return self.forms().filter(function(form) {
      return form.name().toLowerCase().indexOf(filter) > -1
        || form.title().toLowerCase().indexOf(filter) > -1
        || ko.utils.arrayFirst(form.versions(), function(version){
            return (version.publish_date() || '').toLowerCase().indexOf(filter) > - 1
              || (version.retract_date() || '').toLowerCase().indexOf(filter) > - 1
          });
    });
  }).extend({
    rateLimit: {
      method: 'notifyWhenChangesStop',
      timeout: 400
    }
  });

  self.clearSelected = function(){
    self.selectedForm(null);
    self.showEditor(false);
  };

  self.startEditor = function(){
    self.clearSelected();
    self.selectedForm(new Form());
    self.showEditor(true);
  };

  self.startUploader = function(){
    self.clearSelected();
    $('<input type="file" multiple />').click().on('change', function(event){
        var upload = new FormData();
        event.target.files.forEach(function(file){
          upload.append('files', file);
        });

        $.ajax({
          url: window.location,
          type: 'POST',
          data: upload,
          headers: {'X-CSRF-Token': $.cookie('csrf_token')},
          processData: false,  // tell jQuery not to process the data
          contentType: false,  // tell jQuery not to set contentType
          error: handleXHRError({logger: self.errorMessage}),
          beforeSend: function(){
            self.isUploading(true);
          },
          success: function(data, textStatus, jqXHR){

            var updated = data.forms.map(function(raw_forms){
              var form = ko.utils.arrayFirst(self.forms(), function(form) {
                return form.name() == raw_form.name;
              });

              if (form) {
                form.update(raw_form);
              } else {
                form = new Form(raw_form);
                self.forms.push(form);
              }

              return form;
            });

            self.sortForms();

            // Don't overwhelm the user by scrolling to multiple form entries
            if (data.forms.length == 1){
              self.lastUpdatedForm(updated.pop())
            }
          },
          complete: function(jqXHR, textStatus){
            $(event.target).remove();
            self.isUploading(false);
          }
        });
    });
  };

  self.doSave = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: window.location,
        method: 'POST',
        data: ko.toJSON(self.selectedForm()),
        contentType: 'application/json; charset=utf-8',
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errroMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          var form = new Form(data);
          self.forms.push(form);
          self.sortForms();
          self.lastUpdatedForm(form);
          self.clearSelected();
        },
        complete: function(jqXHR, textStatus){
          self.isSaving(false);
        }
      });
    }
  };

  self.sortForms = function(){
    self.forms.sort(function(a, b){
      return a.name().localeCompare(b.name());
    });
  };

  // Get initial data
  $.getJSON(window.location, function(data) {
    self.forms(data.forms.map(function(value){ return new Form(value); }));
    self.isReady(true);
  });
}
