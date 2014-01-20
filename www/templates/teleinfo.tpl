%def rightblock():
    <h1>Teleinfo</h1>
    <div style="border:2px solid;border-radius:12px;padding:10px;">
        <h2 style="margin-top:-12px;margin-right:-12px;margin-left:-12px; border-top-left-radius:12px; border-top-right-radius:12px;text-align:center; color: gray; background-color:lightgray;">
        Relevés</h2>
	    Date de contrat: <input type="text" id="datepicker3" style="width:100px;"/>
	                     <input type="text" id="datepicker4" style="width:100px;"/>
	                     <input type='button' value='Calculer' id='btnGetContractInfo'>
	                     </br>
	    Différence entre les 2 dates: <div id='contractInfo'></div>
	    <table border="1">
	    <tr>
	        <th>Id compteur</th>
	        <th>Index initial (kWh)</th>
	        <th>Index final (kWh)</th>
	        <th>Ecart (kWh)</th>
	    </tr>
	    <tbody id ='tableBody'></tbody>
	
	    </table>
    </div>
    <br>
    <div style="border:2px solid;border-radius:12px;padding:10px;">
        <h2 style="margin-top:-12px;margin-right:-12px;margin-left:-12px; border-top-left-radius:12px; border-top-right-radius:12px;text-align:center; color: gray; background-color:lightgray;">
        Graphique</h2>
	    <p>Date de début: <input type="text" id="datepicker1" style="width:100px;"/>
	       Date de fin: <input type="text" id="datepicker2" style="width:100px;"/>
	       <input type='button' value='Rafraichir' id='btnRefreshGraph'>
	       </p>
	    <form>
	        Compteur:
	        <select name="counter1" id="cbCounter1"></select>
	        
	        <input name="counterName" id="iCounterName" type="text">
	        <input type='button' value='Changer le nom' id='btnSetName'>
	    </form>
	        
	    <div id="chart1" style="height:auto;width:100%;max-height:400px;max-width:800px;"></div>
	    <div id="chart2" style="height:auto;width:100%;max-height:400px;max-width:800px;"></div>
    </div>

%end

%def jscript():
<script>

$(document).ready(function() {
	var plot1;
	var plot2;

    var ajaxDataRendererValue = function(url, plot, options) {
        var ret = null;
        $.ajax({
          // have to use synchronous here, else the function 
          // will return before the data is fetched
          async: false,
          url: url,
          data: "date1=" + options['date1'] + "&date2=" + options['date2'] + "&counterId=" + options['counterId'],
          dataType:"json",
          success: function(data) {
        	  plot.legend.labels = data[0];
              ret = data[1];
          }
        });

        return ret;
    };
    
    //Combo box
    function populateComboBox() {
   	      $("#datepicker1").datepicker({ dateFormat: "dd/mm/yy" });
          $("#datepicker2").datepicker({ dateFormat: "dd/mm/yy" });
          $("#datepicker3").datepicker({ dateFormat: "dd/mm/yy" });
          $("#datepicker4").datepicker({ dateFormat: "dd/mm/yy" });

    	  $("#datepicker1").datepicker( "setDate", "-1m" );
    	  $("#datepicker2").datepicker( "setDate", "0" );
          $("#datepicker3").datepicker( "setDate", "-1y" );
          $("#datepicker4").datepicker( "setDate", "0" );
          
          $.getJSON('teleinfo_counter_id.json', {}, function(data) {
              var select1 = $('#cbCounter1');
              $('option', select1).remove();
              
              select1.append("<option value='-1'>Tous les compteurs</option>")
              $.each(data, function(index, value) {
                  select1.append("<option value='" + value[0] + "'>" + value[1] + "</option>");
              });
              
              //Draw charts after populating combobox
              updateGraphs();
          });
    };
      
    
    function updateGraph1() {
        if (plot1) { plot1.destroy(); }
        
        plot1 = $.jqplot('chart1', "/teleinfo_values_byday.json", {
            dataRenderer: ajaxDataRendererValue,
            dataRendererOptions: { 
                date1: formatDate($("#datepicker1").datepicker("getDate")),
                date2: formatDate($("#datepicker2").datepicker("getDate")),
                counterId:$('#cbCounter1 option:selected').val()
            },
            title:'Evolution journalière (Wh)',
            seriesDefaults:{
                lineWidth:2, 
                markerOptions:{style:'square'}
            },
           
            axes:{
                xaxis:{
                renderer:$.jqplot.DateAxisRenderer,
                tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
                tickOptions:{angle: 90, formatString:'%#d %b'},
                tickInterval:'1 day'
                },
            },
            highlighter: {
                   show: true,
                   sizeAdjust: 7.5
            },
            cursor:{
                show: true,
                zoom:true,
                constrainZoomTo: 'x',
            },
            legend: {
                show: true,
                placement: 'outsideGrid',
            },
        });
    }    
    
    function updateGraph2() {
        if (plot2) { plot2.destroy(); }
        
        plot2 = $.jqplot('chart2', "/teleinfo_index_byday.json", {
            dataRenderer: ajaxDataRendererValue,
            dataRendererOptions: { 
                date1: formatDate($("#datepicker1").datepicker("getDate")), 
                date2: formatDate($("#datepicker2").datepicker("getDate")), 
                counterId:$('#cbCounter1 option:selected').val()
            },
            title:'Index (Wh) (indice de départ à 0 si plusieurs compteurs)',
            seriesDefaults:{
            	showMarker:false,
            	lineWidth:1
            },
            axes:{
                xaxis:{
                renderer:$.jqplot.DateAxisRenderer,
                tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
                tickOptions:{angle: 90, formatString:'%#d %b'},
                tickInterval:'1 day'
                },
            },
            highlighter: {
                   show: true,
                   sizeAdjust: 7.5
            },
            cursor:{
                show: true,
                zoom:true,
                //constrainZoomTo: 'x',
            },
            legend: {
                show: true,
                placement: 'outsideGrid',
            },

        });
    }
    
    function updateContractInfo() {
    	var ret = null;
    	$.ajax({url:'/teleinfo_delta_from_date.json',
    		data: "date1=" + formatDate($("#datepicker3").datepicker("getDate")) + "&date2=" + 
    				formatDate($("#datepicker4").datepicker("getDate")) + "&counterId=" + $('#cbCounter1 option:selected').val(),
			dataType:"json",
            success: function(data) {
            	$("#tableBody").html("");
            	$.each(data, function(id, values) {
            		var table = "<tr><th>" + id + "</th>";
            		table += "<td>" + values[0]/1000 + "</td>";
            		table += "<td>" + values[1]/1000 + "</td>";
            		table += "<td>" + values[2]/1000 + "</td></tr>";
            		
            		$("#tableBody").append(table);
                });
            }
            
    		});
    	
    	
    	
    }
    
    function updateGraphs() {
    	$("#iCounterName").val($('#cbCounter1 option:selected').text());
    	
    	updateGraph1();
    	updateGraph2();
    }
    
    function formatDate(my_date) {
    	year = my_date.getFullYear();
    	month = my_date.getMonth() + 1;
    	day = my_date.getDate();
    	
    	if(day < 10) {
    		strDay = "0" + day;
    	} else {
    		strDay = "" + day;
    	}
        if(month < 10) {
            strMonth = "0" + month;
        } else {
        	strMonth = "" + month;
        }    	
    	return year + "_" + strMonth + "_" + strDay;
    }
    
    //Events handlers
    $("#btnSetName").click(function(){
        $.ajax({
        	type: "GET",
        	url: "/teleinfo_set_counter_id.json",
        	data: "counterId=" + $('#cbCounter1 option:selected').val() + "&counterName=" + $("#iCounterName").val(),
        	dataType: "json",
        	success: function(data) {
        		alert(data);
        	},
	        error: function(data){
	            alert("Impossible de changer le nom !\n");
	            //alert(data.responseText);
            }
        });
        
    });
    
    $("#btnGetContractInfo").click(function(){
    	updateContractInfo();
        });
    $("#btnRefreshGraph").click(function(){
    	updateGraphs();
        });
    
    
    
    $('#cbCounter1').change(updateGraphs);
    populateComboBox();
    
    //Update delta values
    updateContractInfo();

});


</script>

%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title, login=login