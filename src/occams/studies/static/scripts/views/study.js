function StudyView(){
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.study = ko.mapping.fromJSON($('#study-data').text());

  //self.selectedForms = ko.observableArray();
  //self.hasSelectedForms = ko.computed(function(){
    //return self.selectedForms().length > 0;
  //});

  //self.onClickForm = function(item, event){
    //var $element = $(event.target)
      //, value = $element.val();
    //if ($element.prop('checked')){
      //console.log('adding', value);
      //self.selectedForms.push(value);
    //} else {
      //console.log('removing', value);
      //self.selectedForms.remove(value);
    //}
    //return true;
  //}

  //self.startFormAdd = function(){
  //};

  //self.startEdit = function(){
  //};

  //self.startDelete = function(){
  //};

  // Object initalized, set flag to display main UI
  self.isReady(true);
}

+function($){
  $(document).ready(function(){
    var $view = $('#study');
    if ($view.length > 0){
      ko.applyBindings(new StudyView(), $view[0]);
    }
  });
}(jQuery);



/*
        <tbody>
          <tr tal:repeat="ecrf context.schemata">
            <th class="ecrf"><span>${ecrf.title}</span></th>
            <!--! The rest of the columns are the cycles,
                  just loop through them (skip the first since
                  it's the ecrf) -->
            <tal:cycles repeat="enabled ecrf">
              <td tal:condition="not:repeat['enabled'].start">
                <span tal:condition="enabled" class="glyphicon glyphicon-ok"></span>
              </td>
            </tal:cycles>
          </tr>
        </tbody>
*/
