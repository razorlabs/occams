/**
 * Application view model
 */
function StatusViewModel() {
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
      url: export_.delete_url,
      method: 'POST',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      success: function(data, textStatus, jqXHR){
        // Refresh the current page
        self.selectedExport(null);
        self.exports.remove(export_);
        location.hash = '/' + self.pager().page();
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
    var query = {page: page},
        url = window.location.pathname;
    $.get(url, query, function(data){
      if (history.pushState){
        history.pushState(query, page, url);
      }
      self.pager(ko.mapping.fromJS(data.pager));
      self.exports(data.exports.map(function(item){
        return new Export(item);
      }));
      self.ready(true);
    });
  };

  self.onPageClick = function(item, event){
    self.loadPage($(event.target).data('page'));
  };

  +function(){
    /**
     * Configures Socket.io to listen for progress notifications
     */
    // Use the template-embedded socket.io URL
    var socket = io.connect('/export', {
      resource: $('body').data('socket-io-resource')});
    socket.on('connect', function(){
      socket.on('export', function(data){
        self.exports().every(function(export_){
           // find the appropriate export and update it's data
          if (export_.id == data['export_id']) {
            ko.mapping.fromJS(data, {}, export_);
            return false; // "break"
          }
          return true;
        });
      });
    });

    var query = parse_url_query();
    if (query.page !== undefined){
      console.log(query);
      self.loadPage(query.page);
    }
  }();
}
