%def rightblock():
	<h1>Temps réel</h1>

    <div class="borderRound">
    <h2>Rafraichissement</h2>
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
    </div>
    <br/>
    
    <div class="borderRound">
    <h2>Statut</h2>
    Dernière mise à jour: <span id="div_lastUpdate"></span>
    <div id="div_status"></div>
    </div>
    
    <br/>

    <div class="borderRound">
    <h2>Puissance</h2>
    <div id="chart2" class="chartGauge"></div>
    <div id="chart3" class="chartGauge"></div>
    </div>
    
    <br/>
    
    <div class="borderRound">
    <h2>Courant / Tension</h2>
    <div id="chart4" class="chartGauge"></div>
    <div id="chart5" class="chartGauge"></div>
    </div>    

    <br/>
    
    <div class="borderRound">
    <h2>Température</h2>
    <div id="chart1" class="chartGauge"></div>
    </div>    
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
	    //Get last update time
	    var lastUpdate = ajaxDataRendererValue("/real_time_data.json", null, { key: "LastUpdate" });
	    timeStamp = parseInt($(lastUpdate)[0]);
	    
	    var options = {
            weekday: 'long',
            month: 'short',
            year: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric'
            },
        intlDate = new Intl.DateTimeFormat( undefined, options );
        formattedDate = intlDate.format(new Date(1000 * timeStamp));   
	    
	    $("#div_lastUpdate").text(formattedDate);

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
	               intervalColors:['#93b75f', '#E7E658', '#cc6666'],
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
