function feed()
  {
  $(function() {
     //$SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
     $.getJSON(                            //Get some values from the server
        $SCRIPT_ROOT + '/get_values',      // At this URL
        {},                                // With no extra parameters
        function(data)                     // And when you get a response
        {
          $("#all_data").empty().append(data.all_data);  // Write all_data into the #all_data element
          $("#current_state").empty().append(data.current_state);  // Write all_data into the #all_data element
          $("#time_now").text(data.time_now);  // Write all_data into the #all_data element
        });
        });

        setTimeout(feed, 60000); // updates once per minute
  }

  feed();