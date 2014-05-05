+function($){
  'use strict';

  /**
   * Manages form listing
   */
  function FormListView() {

    var self = this;

    self.ready = ko.observable(false);
    self.forms = ko.observableArray([]);

    self.addForm = ko.observable();

    self.launchCreateForm = function(data, event){
      $.ajax($(event.currentTarget).attr('href'), {
        type: 'GET',
        success: function(result){
          self.addForm(ko.mapping.fromJS(result, {}, {
            onSubmit: self.onCreateSubmit
          }));
        }
      });
    }

    self.onCreateSubmit= function(element){
      var $form = $(element);
      $.ajax({
        url: $form.attr('action'),
        type: $form.attr('method'),
        data: $form.serialize(),
        success: function(result){
          switch (result.type) {
            case 'content':
              self.addForm(null);
              self.forms.push(ko.mapping.fromJS(result))
              self.forms.sort(function(left, right){
                // It should NEVER be equal...
                return left.name() < right.name() ? -1 : 1;
              });
              break;
            case 'form':
              // Only update the fields
              self.addForm().fields(ko.mapping.fromJS(result.fields));
              break;
            default:
              console.log('Unexpected result: ' + result)
              break;
          }
        }
      });
    };

    // Get initial data
    $.getJSON(window.location, function(data) {
        self.forms($.map(data, ko.mapping.fromJS));
        self.ready(true);
    });

  };

  /**
   * Registers the view model only if we're in the target page
   */
  $(document).ready(function(){

    var element = $('#home');
    if ( element.length > 0){
      ko.applyBindings(new FormListView(), element[0]);
    }

  });

}(jQuery);
