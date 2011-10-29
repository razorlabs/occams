(function($) {
 $(document).ready(function(){
     
   var setupEditor = function(){
       // Instantiate the editor so we have access to it in other scopes
       window.aceEditor = ace.edit('editor');
       
       var aceEditor = window.aceEditor 
       var XmlMode = require('ace/mode/xml').Mode;
       var sourceField = $('.xml-widget > textarea')[0];
       
       aceEditor.setTheme('ace/theme/twilight');
       aceEditor.getSession().setMode(new XmlMode());
       
       if (sourceField)
       {
           aceEditor.getSession().setValue(sourceField.value);
           aceEditor.setReadOnly(false);
       } 
       else
       {
           editor.setHighlightActiveLine(false);
           aceEditor.setReadOnly(true);
       }
   };
   
   setupEditor();
   
   $('form').submit(function(event){
       var aceEditor = window.aceEditor
       var sourceField = $('.xml-widget > textarea')[0];
       
       // Disable so that clickhappy folk don't keep editing while submitting
       aceEditor.setReadOnly(true);
       
       editorContent = aceEditor.getSession().getValue();
       sourceField.value = editorContent
   });
   
 });
})(jQuery);