/**
 * Groups an array into sub-arrays based on a the grouping function.
 * http://codereview.stackexchange.com/a/37132
 */
function groupBy(array, groupingFunc) {
  "use strict";

  var groups = {};

  array.forEach(function(value){
    var hashableKey = JSON.stringify(groupingFunc(value));
    groups[hashableKey] = groups[hashableKey] || [];
    groups[hashableKey].push(value);
  });

  return Object.keys(groups).map(function(hashableKey){
    return groups[hashableKey];
  });
}
