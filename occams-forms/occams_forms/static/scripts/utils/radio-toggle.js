/**
 * Enables all radio buttons to un-check themselves if they are clicked and are
 * already checked. Also extends this functionality to the corresponding labels
 * for the radio buttons as well.

 * TODO: Doesn't work quite well when a form is autofilled between refreshes.
 */
$(function(){
  'use strict';
  $(document.body).on('click', ':radio', function(event){
    var datakey = 'radio-previous',
        $radio = $(event.target),
        previous = $radio.data(datakey);

    if (previous === undefined){
      previous = $radio.attr('checked') === 'checked';
    }

    $radio.prop('checked', !previous);
    $radio.data(datakey, !previous);
  });
});
