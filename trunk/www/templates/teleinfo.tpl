%def rightblock():
    <h1>Teleinfo</h1>
    <p>Date de début: <input type="text" id="datepicker1" style="width:100px;"/>
       Date de fin: <input type="text" id="datepicker2" style="width:100px;"/></p>
    <form>
        Compteur:
        <select name="counter1" id="cbCounter1"></select>
        
        <input name="counterName" id="iCounterName" type="text">
        <input type='button' value='Changer le nom' id='btnSetName'>
    </form>
        
    <div id="chart1" style="height:auto;width:100%;max-height:400px;max-width:800px;"></div>
    <div id="chart2" style="height:auto;width:100%;max-height:400px;max-width:800px;"></div>


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
        	  //plot.axes.xaxis.ticks = data[1];
              ret = data[2];
              
              //console.log(data[0]);
              //console.log(data[1]);
              //console.log(data[2]);
          }
        });

        return ret;
    };
    
    //Combo box
    function populateComboBox() {
   	      $("#datepicker1").datepicker({ dateFormat: "dd/mm/yy" });
    	  $("#datepicker2").datepicker({ dateFormat: "dd/mm/yy" });

    	  $("#datepicker1").datepicker( "setDate", "-1m" );
    	  $("#datepicker2").datepicker( "setDate", "0" );
    	  
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
        
        plot1 = $.jqplot('chart1', "/teleinfo_all_data.json", {
            dataRenderer: ajaxDataRendererValue,
            dataRendererOptions: { 
                date1: formatDate($("#datepicker1").datepicker("getDate")),
                date2: formatDate($("#datepicker2").datepicker("getDate")),
                counterId:$('#cbCounter1 option:selected').val()
            },
            title:'Evolution journalière (Wh)',
            seriesDefaults:{
                renderer:$.jqplot.BarRenderer,
                rendererOptions: {fillToZero: true},
                pointLabels: { show: false, formatString: '%d'},
                rendererOptions: {barPadding: 0, barMargin: 2, barWidth:8 },
            },
            axes:{
                xaxis:{
                renderer:$.jqplot.DateAxisRenderer,
                tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
                tickOptions:{angle: 90, formatString:'%#d %b'},
                tickInterval: '1 day',
                },
            },
            highlighter: {
                   show: true,
                   sizeAdjust: 0
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
    
    function updateGraph1_line() {
        if (plot1) { plot1.destroy(); }
        
        plot1 = $.jqplot('chart1', "/teleinfo_all_data.json", {
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
        
        plot2 = $.jqplot('chart2', "/teleinfo_rawdata.json", {
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
                tickOptions:{angle: 90, },
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
	            alert("Impossible de changer le nom !");
            }
        });
        
    });  
    
    $('#cbCounter1').change(updateGraphs);
    populateComboBox();
    

});


</script>

%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title