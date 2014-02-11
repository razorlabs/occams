/**
 * Listens for export notifications and updates the page progress bars.
 */

+function($){
  'use strict';

  function Export(data) {
    var self = this;

    ko.mapping.fromJS(data,  {
        observe: ['status', 'count', 'total', 'file_size']
    }, self);

    self.progress = ko.computed(function(){
      return (self.count() / self.total()) * 100;
    }).extend({ throttle: 1 });;
  }

  function StatusViewModel() {
    var self = this;

    self.ready = ko.observable(false)
    self.pager = ko.observable();
    self.exports = ko.observableArray([]);

    var socket = io.connect('/export');

    socket.on('progress', function(data){
      $.each(self.exports(), function(i, export_) {
        if (export_.id == data['export_id']) {
          ko.mapping.fromJS(data, {}, export_);
          return false; // "break"
        }
      });
    });

    // Client-side routes
    Sammy(function() {
        this.get('#/:page', function() {
            $.get("/exports/status", {page: this.params.page}, function(data){
              self.pager(ko.mapping.fromJS(data.pager));
              self.exports($.map(data.exports, function(item) {
                return new Export(item);
              }));
              self.ready(true);
            });
        });
    }).run('#/1');

  }

  $(document).ready(function(){
    var $view = $('#export_status');
    if ( $view.length > 0) {
      ko.applyBindings(new StatusViewModel(), $view[0]);
    }
  });

}(jQuery);
