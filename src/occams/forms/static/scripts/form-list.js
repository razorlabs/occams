/**
 * Manages form listing
 */

function FormListView() {

  var self = this;

  self.ready = ko.observable(false);      // Flag unhide body

  self.action = ko.observable();           // Current form in modal

  self.forms = ko.observableArray([]);    // Master list of forms
  self.filter = ko.observable();          // Filter string (i.e. search)

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
            return version.status().toLowerCase().indexOf(filter) > - 1
              || (version.publish_date() || '').toLowerCase().indexOf(filter) > - 1
              || (version.retract_date() || '').toLowerCase().indexOf(filter) > - 1
          });
    });
  }).extend({
    rateLimit: {
      method: 'notifyWhenChangesStop',
      timeout: 400
    }
  });

  self.launchAddForm = function(data, event){
    $.getJSON($(event.currentTarget).data('target'), function(data){
      self.action(new AddView(data));
    });
  };

  self.launchUploadForm = function(data, event){
    $.getJSON($(event.currentTarget).data('target'), function(data){
      self.action(new UploadView(data));
    });
  };

  // Get initial data
  $.getJSON(window.location, function(data) {
      self.forms($.map(data, ko.mapping.fromJS));
      self.ready(true);
  });

}


function UploadForm(data){
  var self = this;

  self.fields = ko.mapping.fromJS(fields);

  self.onSubmit = function(element){
  };
}


function AddForm(data){
  var self = this;

  self.fields = ko.mapping.fromJS(fields);

  self.onSubmit = function(element){
    var $form = $(element);
    $.ajax({
      url: $form.attr('action'),
      type: $form.attr('method'),
      data: $form.serialize(),
      success: function(result){
        switch (result.type) {
          case 'content':
            self.form(null);
            self.forms.push(ko.mapping.fromJS(result))
            self.forms.sort(function(left, right){
              // It should NEVER be equal...
              return left.name().toLowerCase() < right.name().toLowerCase() ? -1 : 1;
            });
            break;
          case 'form':
            // Only update the fields
            self.form().fields(ko.mapping.fromJS(result.fields));
            break;
          default:
            console.log('Unexpected result: ' + result)
            break;
        }
      }
    });
  };
}


/**
 * Registers the view model only if we're in the target page
 */
$(document).ready(function(){

  var element = $('#home');
  if ( element.length > 0){
    ko.applyBindings(new FormListView(), element[0]);
  }

});
