/**
 * Export codebook view models
 *
 * Registers Knockout obervables to update codebook panels
 */
+function($){
  'use strict';

  /**
   * Application view model
   */
  function CodebookViewModel() {
    var self = this;

    self.ready = ko.observable(false);        // Used to signal that page is ready
    self.loading = ko.observable(false);      // Used for display when AJAX is done
    self.name = ko.observable();
    self.title = ko.observable();
    self.rows = ko.observableArray([]);      // Codebook rows

    // Client-side routes
    Sammy(function() {
        /**
         * Fetches the specified  page contents and updates the view model
         */
        this.get('#/:file', function(){
          var e = $('[data-name="' + this.params.file + '"]');
          self.name(e.data('name'));
          self.title(e.data('title'));
          self.loading(true);
          // Use current window location so we don't hard-code app URLs
          $.get(window.location, {file: this.params.file}, function(data){
            self.rows(data);
            self.loading(false);
          });
        });
        this.get('%/', function(){});
    }).run('#/');

    self.ready(true)
  }

  /**
   * Registers the view model only if we're in the target page
   * TODO: would be nice to figure this out in RequireJS
   */
  $(document).ready(function(){
    var $view = $('#export_codebook');
    if ( $view.length > 0 ) {
      ko.applyBindings(new CodebookViewModel(), $view[0]);
    }

  });

}(jQuery);
