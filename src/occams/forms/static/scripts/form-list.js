/**
 * Manages form listing
 */

function FormListView() {

  var self = this;

  self.isReady = ko.observable(false);          // Flag unhide body
  self.isSaving = ko.observable(false);
  self.isUploading = ko.observable(false);

  self.forms = ko.observableArray([]);          // Master list of forms
  self.filter = ko.observable();                // Filter string (i.e. search)

  self.lastUpdatedForm = ko.observable();       // Keep track of last updated form
  self.selectedForm = ko.observable();          // Current form in modal
  self.selectedFormErrors = ko.observable();
  self.showEditor = ko.observable(false);
  self.showUploader = ko.observable(false);

  /**
   *  Filtered forms based on filter string>
   */
  self.filteredForms = ko.computed(function(){
    var filter = self.filter();

    // No filter, return master list
    if (!filter) {
      return self.forms();
    }

    filter = filter.toLowerCase();

    return ko.utils.arrayFilter(self.forms(), function(form) {
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
    self.showUploader(false);
  };

  self.startEditor = function(){
    self.clearSelected();
    self.selectedForm(new Form({}));
    self.showEditor(true);
  };

  self.startUploader = function(){
    self.clearSelected();
    self.showUploader(true);
    $('<input type="file" multiple />').click().on('change', function(event){
        self.isUploading(true);

        var upload = new FormData();
        $.each(event.target.files, function(i, file){
          upload.append('files', file);
        });

        $.ajax({
          url: window.location,
          type: 'POST',
          data: upload,
          headers: {'X-CSRF-Token': $.cookie('csrf_token')},
          processData: false,  // tell jQuery not to process the data
          contentType: false,  // tell jQuery not to set contentType
          error: function(jqXHR, textStatus, thrownExeption){
            data = jqXHR.responseJSON;
            if (!data || !data.validation_errors){
              console.log('A server-side error occurred');
              console.log(data);
              return;
            }
            self.selectedFormErrors(data.validation_errors);
          },
          success: function(data, textStatus, jqXHR){
            var updated = self.updateForms(data.forms);
            // Don't overwhelm the user by scrolling to multiple form entries
            if (data.forms.length == 1){
              self.lastUpdatedForm(updated.pop())
            }
          },
          complete: function(jqXHR, textStatus){
            self.isUploading(false);
          }
        });
    });
  };

  self.doSave = function(){
    var form = self.selectedForm();
    self.isSaving(true);
    $.ajax({
      url: window.location,
      type: 'POST',
      data: ko.mapping.toJS(form),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      //contentType: 'application/json',
      error: function(jqXHR, textStatus, thrownExeption){
        data = jqXHR.responseJSON;
        if (!data || !('validation_errors' in data)){
          console.log('A server-side error occurred');
          return;
        }

        var errors = data.validation_errors;
        for (prop in form){
          if ('errors' in form[prop]){
            if (prop in data.validation_errors){
              form[prop].errors(data.validation_errors[prop]);
            } else {
              form[prop].errors([]);
            }
          }
        }
      },
      success: function(data, textStatus, jqXHR){
        var updated = self.updateForms(data.forms);
        self.lastUpdatedForm(updated.pop())
        self.clearSelected();
      },
      complete: function(jqXHR, textStatus){
        self.isSaving(false);
      }
    });
  };

  /**
   * Updates view forms listing with incoming raw form data
   * Returns a list of updated form models.
   */
  self.updateForms = function(raw_forms){
    return ko.utils.arrayMap(raw_forms, function(raw_form){
      var form = ko.utils.arrayFirst(self.forms(), function(form) {
        return form.name() == raw_form.name;
      });

      if (form) {
        form.title(raw_form.title);
        form.versions(ko.utils.arrayMap(raw_form.versions, function(raw_version){
          return new Version(raw_version);
        }));
      } else {
        form = new Form(raw_form);
        self.forms.push(form);
        self.forms.sort(function(left, right){
          return left.name().toLowerCase() < right.name().toLowerCase() ? -1 : 1;
        });
      }

      return form;
    });
  };

  // Get initial data
  $.getJSON(window.location, function(data) {
    console.log(data);
    self.forms(ko.utils.arrayMap(data.forms, function(form_data){
      return new Form(form_data);
    }));
    self.isReady(true);
  });
}


function Form(data) {
  var self = this;
  self.name = ko.observable(data.name).extend({validateable: {}});
  self.title = ko.observable(data.title).extend({validateable: {}});
  self.has_private = ko.observable(data.has_private);
  self.versions = ko.observableArray(!data.versions ? [] : ko.utils.arrayMap(data.versions, function(version_data){
    return new Version(version_data);
  }));
}


function Version(data) {
  var self = this;
  self.__src__ = ko.observable(data.__src__);
  self.publish_date = ko.observable(data.publish_date);
  self.retract_date = ko.observable(data.retract_date);
}


/**
 * Registers the view model only if we're in the target page
 */
$(document).ready(function(){
  if ($('#form_list').length < 1){
    return;
  }

  ko.applyBindings(new FormListView());
});
