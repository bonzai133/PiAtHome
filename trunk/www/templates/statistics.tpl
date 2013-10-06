%def rightblock():
	<h1>Statistiques</h1>

    <div id="total">Energie totale: </div>
    <div id="hours">Heures de fonctionnement: </div>
    <br>
    
    <table border="1">
	    <tr>
		    <th></th>
		    <th>Période en cours</th>
		    <th>Période précédente</th>
	    </tr>
        <tr>
            <th>Jour</th>
            <td id='today'></td>
            <td id='yesterday'></td>
        </tr>
        <tr>
            <th>Mois</th>
            <td id='month'></td>
            <td id='last_month'></td>
        </tr>
        <tr>
            <th>Année</th>
            <td id='year'></td>
            <td id='last_year'></td>
        </tr>    
    </table>
	
%end

%def jscript():
<script>
$(document).ready(function(){
      var ajaxDataRendererValue = function(url, plot, options) {
            var ret = null;
            $.ajax({
              // have to use synchronous here, else the function 
              // will return before the data is fetched
              async: false,
              url: url,
              data: "key=" + options['key'],
              dataType:"json",
              success: function(data) {
                ret = data;
              }
            });
            return ret;
          };

    //Get status
    var json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KDY" });
    $("#today").append($(json_value)[0] + " Wh");
    
    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KLD" });
    $("#yesterday").append($(json_value)[0] + " Wh");
    
    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KMT" });
    $("#month").append($(json_value)[0] + " kWh");

    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KLM" });
    $("#last_month").append($(json_value)[0] + " kWh");
    
    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KYR" });
    $("#year").append($(json_value)[0] + " kWh");

    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KLY" });
    $("#last_year").append($(json_value)[0] + " kWh");

    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KT0" });
    $("#total").append($(json_value)[0] + " kWh");
    
    json_value = ajaxDataRendererValue("/statistics_data.json", null, { key: "KHR" });
    $("#hours").append($(json_value)[0] + " h");

});
</script>
%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title