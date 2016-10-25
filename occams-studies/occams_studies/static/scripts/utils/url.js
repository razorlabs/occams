function parse_url_query(encoded) {
  'use strict';

  var query = {};

  if (!encoded){
    encoded = window.location.search;
  }

  if (encoded.charAt(0) == '?'){
    encoded = encoded.substring(1);
  }

  encoded.split('&').forEach(function(value){
    if (!value){
      return;
    }

    var pair = value.split('='),
        key = decodeURIComponent(pair[0]),
        value = decodeURIComponent(pair[1]);

    if (key in query){
      query[key].push(value);
    } else {
      query[key] = [value];
    }
  });

  return query;
}

