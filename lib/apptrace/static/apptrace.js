/*!
 * Apptrace JavaScript
 *
 * Copyright 2010, Tobias Rodaebel
 */
$(function () {
  var options = {
    lines: {show: true},
    points: {show: true},
    xaxis: {tickDecimals: 0, tickSize: 1},
    legend: {container: $('#legend'), noColumns: 10}
  };

  function updateData(data) {
    var records = JSON.parse(data);

    var memory_series = {};
    var memory_data = [];

    var details_series = {};
    var details_keys = [];
    var details_data = [];

    if (records.length == 0)
      return null;

    for (i=0; i<records.length; i++) {
      var record = records[i];
      var cumulated_size = 0;

      for (j=0; j<record.entries.length; j++) {
        var entry = record.entries[j];

        if (!details_series[entry.name]) {
          var label = '<a href="/_ah/apptrace/browse'
                    + '?filename=' + entry.filename
                    + '&lineno=' + entry.lineno
                    + '">' + entry.name + '</a>';
          details_series[entry.name] = {label: label, data: []};
          details_keys.push(entry.name);
        }

        details_series[entry.name].data.push([record.index,
                                              entry.dominated_size]);

        cumulated_size += entry.dominated_size;
      }

      if (!memory_series['cumulated']) {
        memory_series['cumulated'] = {label: 'cumulated', data: [],
                                      lines: {fill: true}};
      }

      memory_series['cumulated'].data.push([record.index,
                                            cumulated_size]);
    }
    for (var key in memory_series)
      memory_data.push(memory_series[key]);

    var sorted_keys = details_keys.sort();
    for (k=0; k<sorted_keys.length; k++)
      details_data.push(details_series[sorted_keys[k]]);

    $.plot($('#memory'), memory_data, options);
    $.plot($('#details'), details_data, options);
  }

  $('#refresh').click(function() {
    var button = $(this);
    var url = button.siblings('a').attr('href');
    $.ajax({
      url: url,
      method: 'GET',
      success: updateData
    });
  });

  $('#refresh').click();
});
