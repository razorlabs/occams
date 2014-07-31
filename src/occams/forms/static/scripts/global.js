/**
 * Global settings
 */


$(document).ready(function(){
  $('select').select2();
  $('input[type="datetime"]').datetimepicker();
  $('input[type="date"]').datetimepicker({pickTime: false});
});
