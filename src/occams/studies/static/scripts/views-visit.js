function VisitView(){
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.visit = ko.mapping.fromJSON($('#visit-data').text());

  self.selectedForms = ko.observableArray();
  self.hasSelectedForms = ko.computed(function(){
    return self.selectedForms().length > 0;
  });

  self.onClickForm = function(item, event){
    var $element = $(event.target)
      , value = $element.val();
    if ($element.prop('checked')){
      console.log('adding', value);
      self.selectedForms.push(value);
    } else {
      console.log('removing', value);
      self.selectedForms.remove(value);
    }
    return true;
  }

  self.startFormAdd = function(){
  };

  self.startEdit = function(){
  };

  self.startDelete = function(){
  };

  // Object initalized, set flag to display main UI
  self.isReady(true);
}

+function($){
  $(document).ready(function(){
    var $view = $('#visit');
    if ($view.length > 0){
      ko.applyBindings(new VisitView(), $view[0]);
    }
  });
}(jQuery);
