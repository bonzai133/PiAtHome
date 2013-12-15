%def rightblock():
	<h1>Temps réel</h1>

    Rafraichissement de la page:
    <select id="select_refresh">
        <option value="0">Désactivé</option>
        <option value="10">10 s</option>
        <option value="30">30 s</option>
        <option value="60">1 mn</option>
        <option value="300">5 mn</option>
        <option value="600">10 mn</option>
    </select>
    <div id="div_refresh">Rechargement des données dans <span id="span_timer">0</span> secondes.</div>
    
    <div></div>
    <br/>
    
    <div id="div_status"></div>
    <div></div>
    <div id="chart1" style="height:200px;width:250px;display: inline-block;"></div>
    <div></div>
    <div id="chart2" style="height:200px;width:250px;display: inline-block;"></div>
    <div id="chart3" style="height:200px;width:250px;display: inline-block;"></div>
    <div></div>
    <div id="chart4" style="height:200px;width:250px;display: inline-block;"></div>
    <div id="chart5" style="height:200px;width:250px;display: inline-block;"></div>
    
	<!--http://www.jqplot.com/deploy/dist/examples/meterGauge.html-->
%end

%def jscript():
<script>
$(document).ready(function(){
	var plot1;
	var plot2;
    var plot3;
    var plot4;
    var plot5;
    var seconds;
    var timer_display;
    var timer_refresh;
    
    $('#select_refresh').change( function() {
    	if ($(this).find('option:selected').val() == 0) {
            $("#div_refresh").hide();
            clearTimeout(timer_display);
            clearTimeout(timer_refresh);
    	} else {
            $("#div_refresh").show();

            clearTimeout(timer_display);
            clearTimeout(timer_refresh);

            doUpdate();

            timer_display = setInterval(mytimer, 1000);
        }
    });
    

    function mytimer() {
        seconds --;
    	$("#span_timer").text(seconds);
    }
	
    function doUpdate() {
        updateStatus();
        updateGraph1();
        updateGraph2();
        updateGraph3();
        updateGraph4();
        updateGraph5();
        
        seconds = $('#select_refresh').find('option:selected').val()
        if (seconds != 0) {
        	clearTimeout(timer_refresh);
            timer_refresh = setTimeout(doUpdate, seconds*1000);
        }
    }
    
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

	function updateStatus() {
	    //Get status
	    var current_status = ajaxDataRendererValue("/real_time_data.json", null, { key: "SYS" });
	    $("#div_status").text($(current_status)[0]);
	}
		  
    function updateGraph1() {
    	if (plot1) { plot1.destroy(); }
    	
		plot1 = $.jqplot('chart1', "/real_time_data.json", {
		    dataRenderer: ajaxDataRendererValue,
		    dataRendererOptions: { key: "TKK" },
		    grid: {background: 'transparent'},
		    seriesDefaults: {
		         renderer: $.jqplot.MeterGaugeRenderer,
		         rendererOptions: {
		            label: "Température (°C)",
		            labelPosition: 'bottom',
		            min: 0,
		            max: 60,
		            intervals:[45, 55, 60],
		            intervalColors:['#93b75f', '#E7E658', '#cc6666'],
		        }
		    }
		});
    }
    
    function updateGraph2() {
        if (plot2) { plot2.destroy(); }
        
	    plot2 = $.jqplot('chart2', "/real_time_data.json", {
		   dataRenderer: ajaxDataRendererValue,
		   dataRendererOptions: { key: "PRL" },
		   grid: {background: 'transparent'},
	       seriesDefaults: {
	            renderer: $.jqplot.MeterGaugeRenderer,
	            rendererOptions: {
	        	   label: 'Puissance relative (%)',
	        	   labelPosition: 'bottom',
	               min: 0,
	               max: 100,
	               intervals:[25, 75, 100],
	               intervalColors:['#cc6666', '#E7E658', '#93b75f'],
	           }
	       }
	   });
    }
   
    function updateGraph3() {
        if (plot3) { plot3.destroy(); }

        plot3 = $.jqplot('chart3', "/real_time_data.json", {
	       dataRenderer: ajaxDataRendererValue,
	       dataRendererOptions: { key: "PAC" },
	       grid: {background: 'transparent'},
	       seriesDefaults: {
	            renderer: $.jqplot.MeterGaugeRenderer,
	            rendererOptions: {
	               label: 'Puissance de sortie (W)',
	               labelPosition: 'bottom',
	               min: 0,
	               max: 3000,
	               intervals:[600, 2400, 3000],
	               intervalColors:['#93b75f', '#E7E658', '#cc6666'],
	           }
	       }
	   });
    }
   
    function updateGraph4() {
        if (plot4) { plot4.destroy(); }

		plot4 = $.jqplot('chart4', "/real_time_data.json", {
		    dataRenderer: ajaxDataRendererValue,
		    dataRendererOptions: { key: "UDC" },
		    grid: {background: 'transparent'},
		    seriesDefaults: {
		         renderer: $.jqplot.MeterGaugeRenderer,
		         rendererOptions: {
		            label: "Tension d'entrée (V)",
		            labelPosition: 'bottom',
		            min: 0,
		            max: 600,
		            intervals:[100, 235, 550],
		            intervalColors:['#cc6666', '#E7E658', '#93b75f'],
		        }
		    }
		});
    }
   
    function updateGraph5() {
        if (plot5) { plot5.destroy(); }

		plot5 = $.jqplot('chart5', "/real_time_data.json", {
		    dataRenderer: ajaxDataRendererValue,
		    dataRendererOptions: { key: "IDC" },
		    grid: {background: 'transparent'},
		    seriesDefaults: {
		         renderer: $.jqplot.MeterGaugeRenderer,
		         rendererOptions: {
		            label: "Courant d'entrée (A)",
		            labelPosition: 'bottom',
		            min: 0,
		            max: 11,
		            ticks: [0,1,2,3,4,5,6,7,8,9,10,11],
		            intervals:[3, 8, 11],
		            intervalColors:['#cc6666', '#E7E658', '#93b75f'],
		        }
		    }
		});
    }
   
    /*Init state*/
    $("#div_refresh").hide();
    doUpdate();
   
});
</script>
%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title, login=login