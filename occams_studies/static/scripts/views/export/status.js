/**
 * Application view model
 */
function StatusViewModel(options) {
  var self = this;

  self.ready = ko.observable(false);      // Used for display when AJAX is done
  self.pager = ko.observable();           // Pagination
  self.exports = ko.observableArray([]);  // Current exports in the view

  self.has_exports = ko.computed(function(){
    return self.exports().length > 0;
  });

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
    $.ajax({
      url: export_.delete_url(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      success: function(data, textStatus, jqXHR){
        self.loadPage(self.pager().page);
        self.selectedExport(null);
      }
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

  self.loadPage = function (page){
    $.get(window.location.pathname, {page: page}, function(data){
      self.pager(data.pager);
      self.exports(data.exports.map(function(item){
        return new Export(item);
      }));
      self.ready(true);
    });
  };

  self.onPageClick = function(item, event){
    var $target = $(event.target),
        url = $target.attr('href'),
        page = $target.data('page');

    if (history.pushState){
      history.pushState({}, '', url);
    }

    self.loadPage(page);
  };

  +function(){
    /**
     * Configures Socket.io to listen for progress notifications
     */
    // Use the template-embedded socket.io URL
    var socket = io.connect(options.socketio_namespace, {resource: options.socketio_resource});
    socket.on('connect', function(){
      socket.on('export', function(data){

        var export_ = ko.utils.arrayFirst(self.exports(), function(e){
          return e.id() == data['export_id'];
        });

        if (export_){
          export_.count(data['count']);
          export_.total(data['total']);
          export_.status(data['status']);
          export_.file_size(data['file_size']);
        }

      });
    });

    var query = parse_url_query(),
        page = query.page || 1;

    self.loadPage(page);
  }();
}
