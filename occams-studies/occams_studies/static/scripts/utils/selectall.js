/**
 * Addon to enable "Select All" functionality in tables.
 *
 * The idea is that there's a primary checkbox that, when selected, will apply
 * its value to the slave checkboxes.
 *
 * The primary checkbox is denoted by it's ``data-toggle="selectall"`` attribute.
 *
 * The slave checkboxes are denonted by their ``data-toggle="select"`` attribute.
 * Additionally, a ``data-class`` attribute is required. This value is the CSS class
 * that will be applied to the parent row of the slave.
 */

+function($){
  'use strict';

  /**
   * Event handler for when the primary check box is selected.
   */
  $(document).on('change', 'input[data-toggle=selectall]', function(event){
    var $target = $(event.target);
    $target
      .closest('table')
      .find('input[data-toggle=select]')
      .prop('checked', $target.prop('checked'))
      .change();
  });

  /**
   * Event handler for when a slave check box is selected.
   */
  $(document).on('change', 'input[data-toggle=select]', function(event){
    var $target = $(event.target);
    $target
      .closest('tr')
      .toggleClass($target.data('class'), $target.prop('checked'));
  });

  /**
   * Updates the addon when the DOM is ready.
   */
  $(document).ready(function(){
    $('input[data-toggle=selectall]').change();
  });

}(jQuery);
