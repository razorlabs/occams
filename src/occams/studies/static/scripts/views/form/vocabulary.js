/**
 * Unified select2 options for form selction
 */
function formSelect2Options(element){
  return {
    allowClear: true,
    ajax: {
      data: function(term, page){
        return {vocabulary: 'available_schemata', term: term};
      },
      results: function(data){
        return {
          results: data.schemata.map(function(schema){
            return new StudyForm({schema: schema, versions: [schema]});
          })
        };
      }
    }
  };
}

