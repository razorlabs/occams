/**
 * Application view model
 */
function CodebookViewModel() {
  var self = this;

  self.ready = ko.observable(false);        // Used to signal that page is ready
  self.loading = ko.observable(false);      // Used for display when AJAX is done
  self.selected = ko.observable();
  self.rows = ko.observableArray([]);      // Codebook rows

  self.loadCodebook = function(name){

    var query = {file: name},
        url = window.location.pathname + '?' + $.param(query, true);

    if (!name){
      self.selected(null);
      self.rows([]);

    } else {
      self.loading(true);
      $.get(url, query, function(data){
        self.rows(data);
        self.loading(false);
        self.selected(name);
      });
    }
  };

  self.onSelection = function(item, event){
    self.loadCodebook(event.target.value);
  };

  +function(){
    self.ready(true)
  }();
}
