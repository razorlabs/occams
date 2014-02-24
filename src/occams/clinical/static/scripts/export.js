/**
 * Export status page view models
 *
 * Registers Knockout obervables to update progress of each export task.
 */
+function($){
  'use strict';

  /**
   * An individual Export model
   */
  function Export(data) {
    var self = this;

    ko.mapping.fromJS(data,  {
        // select only the items we want to observe
        observe: ['status', 'count', 'total', 'file_size']
    }, self);

    /**
     * Calculates this export's current progress
     */
    self.progress = ko.computed(function(){
      return (self.count() / self.total()) * 100;
    }).extend({ throttle: 1 });
  }

  /**
   * Application view model
   */
  function StatusViewModel() {
    var self = this;

    self.ready = ko.observable(false);      // Used for display when AJAX is done
    self.pager = ko.observable();           // Pagination
    self.exports = ko.observableArray([]);  // Current exports in the view

    self.csrf_token = ko.observable();      // Prevent XSS attacks

    self.selectedExport = ko.observable();  // Current export being deleted

    /**
     * Marks the export as a candidate for deletion
     */
    self.confirmDelete = function(export_){
      self.selectedExport(export_);
    };

    /**
     * Sends delete request to the server
     */
    self.deleteExport = function(export_) {
      $.post(export_.delete_url, {csrf_token: self.csrf_token()}, function(data){
        // Refresh the current page
        self.selectedExport(null);
        self.exports.remove(export_);
        location.hash = '/' + self.pager().page();
      });
    };

    /**
     * Handles an element being shown by "sliding" it in.
     * (Necessary DOM manipulation evil...)
     */
    self.showElement = function(e) {
      if (self.ready() && e.nodeType === 1) {
        $(e).hide().slideDown();
      }
    };

    /**
     * Handles an element being hidden  by "sliding" it out.
     * (Necessary DOM manipulation evil...)
     */
    self.hideElement = function(e) {
      if (self.ready() && e.nodeType === 1){
        $(e).slideUp(function() {
          $(e).remove();
        })
      };
    }

    /**
     * Configures Socket.io to listen for progress notifications
     */
    // Use the template-embedded socket.io URL
    var socket = io.connect('/export', {
      resource: $('body').data('socket-io-resource')});
    //$('body').data('socket-io-path')})
    socket.on('connect', function(){
      console.log('connected!');
      socket.on('progress', function(data){
        $.each(self.exports(), function(i, export_) {
          // find the appropriate export and update it's data
          if (export_.id == data['export_id']) {
            ko.mapping.fromJS(data, {}, export_);
            return false; // "break"
          }
        });
      });
    });

    // Client-side routes
    Sammy(function() {
        /**
         * Fetches the specified  page contents and updates the view model
         */
        this.get('#/:page', function() {
          // Use current window location so we don't hard-code app URLs
          $.get(window.location, {page: this.params.page}, function(data){
            self.csrf_token(data.csrf_token);
            self.pager(ko.mapping.fromJS(data.pager));
            self.exports($.map(data.exports, function(item){
              return new Export(item);
            }));
            self.ready(true);
          });
        });
    }).run('#/1');

  }

  /**
   * Registers the view model only if we're in the export page
   * TODO: would be nice to figure this out in RequireJS
   */
  $(document).ready(function(){
    var $view = $('#export_status');
    if ( $view.length > 0) {
      ko.applyBindings(new StatusViewModel(), $view[0]);
    }
  });

}(jQuery);
