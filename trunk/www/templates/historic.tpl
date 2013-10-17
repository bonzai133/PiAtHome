%def rightblock():
    <h1>Production annuelle</h1>
    <form>
        Comparer:
        <select name="compare1" id="cbCompare1"></select>
        avec:
        <select name="compare2" id="cbCompare2"></select>
    </form>
    
    <div id="chart1" style="height:auto;width:100%;max-height:400px;max-width:800px;"></div>
    <br><span id="info1"></span>
    <div id="chart2" style="height:auto;width:100%;max-height:200px;max-width:800px;"></div>
%end

%def jscript():
<script>
$(document).ready(function(){
  // Our ajax data renderer which here retrieves a text file.
  // it could contact any source and pull data, however.
  // The options argument isn't used in this renderer.
  var ajaxDataRendererYear = function(url, plot, options) {
    var ret = null;
    $.ajax({
      // have to use synchronous here, else the function 
      // will return before the data is fetched
      async: false,
      url: url,
      data: "year1=" + $('#cbCompare1 option:selected').text() + 
            "&year2=" + $('#cbCompare2 option:selected').text(),
      dataType:"json",
      success: function(data) {
        ret = data;
      }
    });
    return ret;
  };
  var ajaxDataRendererMonth = function(url, plot, options) {
        var ret = null;
        $.ajax({
          // have to use synchronous here, else the function 
          // will return before the data is fetched
          async: false,
          url: url,
          data: "year1=" + $('#cbCompare1 option:selected').text() + 
                "&year2=" + $('#cbCompare2 option:selected').text() +
                "&month=" + options['optionSelectedMonth'],
          dataType:"json",
          success: function(data) {
            ret = data;
          }
        });
        return ret;
      }; 
  //chart bar renderer
  var url_energy_by_year = "./energy_by_year.json";
  var url_energy_by_month = "./energy_by_month.json";
  
  // Can specify a custom tick Array.
  // Ticks should match up one for each y value (category) in the series.
  var ticks_month_full;
  $.getJSON('ticks_monthes_full.json', {}, function(data) { ticks_month_full = data;});
  var ticks_month;
  $.getJSON('ticks_monthes.json', {}, function(data) { ticks_month = data;});
  

  function drawChart1() {
      var my_plot = $.jqplot('chart1', url_energy_by_year, {
          dataRenderer: ajaxDataRendererYear,
          // The "seriesDefaults" option is an options object that will
          // be applied to all series in the chart.
          seriesDefaults:{
              showMarker:false,
          },
          // Custom labels for the series are specified with the "label"
          // option on the series option.  Here a series option object
          // is specified for each series.
          series:[
              {
                  label:$('#cbCompare1 option:selected').text(),
                  renderer:$.jqplot.BarRenderer,
                  rendererOptions: {fillToZero: true},
                  pointLabels: { show: true, formatString: '%d'}
              },
              {
                  label:$('#cbCompare2 option:selected').text(),
                  renderer:$.jqplot.BarRenderer,
                  rendererOptions: {fillToZero: true},
                  pointLabels: { show: true, formatString: '%d'}
                  
              },
              {
                  label: 'Total ' + $('#cbCompare1 option:selected').text(),
                  yaxis: 'y2axis',
                  fill: false,
              },
              {
                  label: 'Total ' + $('#cbCompare2 option:selected').text(),
                  yaxis: 'y2axis',
                  fill: false,
              },
              
          ],
          // Show the legend and put it outside the grid, but inside the
          // plot container, shrinking the grid to accomodate the legend.
          // A value of "outside" would not shrink the grid and allow
          // the legend to overflow the container.
          legend: {
              show: true,
              placement: 'outsideGrid'
          },
          axes: {
              // Use a category axis on the x axis and use our custom ticks.
              xaxis: {
                  renderer: $.jqplot.CategoryAxisRenderer,
                  ticks: ticks_month
              },
              // Pad the y axis just a little so bars can get close to, but
              // not touch, the grid boundaries.  1.2 is the default padding.
              yaxis: {
                  pad: 1.05,
                  tickOptions: {formatString: '%d kWh'},
                  min: 0,
                  max: 500,
                  numberTicks: 5,
              },
              y2axis: {
                  pad: 1.05,
                  tickOptions: {formatString: '%d kWh'},
                  min: 0,
                  max: 5000,
                  numberTicks: 5,
              }
          }
      });
      //my_plot.moveSeriesToBack(2);
      //my_plot.moveSeriesToBack(3);
      
      return my_plot;
  }

  function drawChart2(selected_month) {
      var my_plot = $.jqplot('chart2', url_energy_by_month, {
          dataRenderer: ajaxDataRendererMonth,
          dataRendererOptions: { optionSelectedMonth: selected_month },
          
          // The "seriesDefaults" option is an options object that will
          // be applied to all series in the chart.
          seriesDefaults:{
              renderer:$.jqplot.BarRenderer,
              rendererOptions:{
                  fillToZero: true, 
                  barPadding: 1.05, 
                  barWidth: 6, 
                  barMargin: 3}, 
              showMarker:false,
              pointLabels: { show: true, formatString: '%d'}
          },
          // Custom labels for the series are specified with the "label"
          // option on the series option.  Here a series option object
          // is specified for each series.
          series:[
              {
                  label: ticks_month[selected_month-1] + " " +$('#cbCompare1 option:selected').text(),
              },
              {
                  label: ticks_month[selected_month-1] + " " + $('#cbCompare2 option:selected').text(),
              },
          ],
          // Show the legend and put it outside the grid, but inside the
          // plot container, shrinking the grid to accomodate the legend.
          // A value of "outside" would not shrink the grid and allow
          // the legend to overflow the container.
          legend: {
              show: true,
              placement: 'outsideGrid'
          },
          axes: {
              // Use a category axis on the x axis and use our custom ticks.
              xaxis: {
                  renderer: $.jqplot.CategoryAxisRenderer,
              },
              // Pad the y axis just a little so bars can get close to, but
              // not touch, the grid boundaries.  1.2 is the default padding.
              yaxis: {
                  //pad: 1.05,
                  tickOptions: {formatString: '%d kWh'},
                  //min: 0,
                  //max: 25,
                  //numberTicks: 5,
              }
          }
      });
      
      return my_plot;
  }
  
  //Combo box
  function populateCompareComboBox() {
       
        $.getJSON('combobox_years_data.json', {}, function(data) {
            var select1 = $('#cbCompare1');
            var select2 = $('#cbCompare2');
            $('option', select1).remove();
            $('option', select2).remove();
            
            $.each(data, function(index, value) {
                select1.append("<option>" + value + "</option>")
                select2.append("<option>" + value + "</option>")
            });
            
            if ($('#cbCompare2 option').length > 0) {
            	$('#cbCompare2').get(0).selectedIndex = 1;
            }
            
            //Draw chart1 after populating combobox
            refreshPlot1();
        });
    };
  
  var plot1;
  var plot2;
  function refreshPlot1() {
    if(plot2) { 
         $('#info1').html("");
         plot2.destroy(); 
    }
    if(plot1) { 
        plot1.destroy(); 
    }
    plot1 = drawChart1();
  }
      
  //Bind a listener to the "jqplotDataClick" event.
  $('#chart1').bind('jqplotDataClick', 
    function (ev, seriesIndex, pointIndex, data) {
      //$('#info1').html('series: '+seriesIndex+', point: '+pointIndex+', data: '+data);
      $('#info1').html( "Détail du mois " + ticks_month_full[pointIndex]);
      if(plot2) { plot2.destroy(); }
      plot2 = drawChart2(pointIndex+1);
    }
  );
  
  //Bind resize browser event
  $(window).resize(function() {
	  $.each(plot1.series, function(index, series) { series.barWidth = undefined; });
	  plot1.replot( { resetAxes: true } );

	  $.each(plot2.series, function(index, series) { series.barWidth = undefined; });
	  plot2.replot( { resetAxes: true } );
      
      
  });


  
  $('#cbCompare1').change(refreshPlot1);
  $('#cbCompare2').change(refreshPlot1);  
  
  //Handle combo box selection
  populateCompareComboBox();
  
});
</script>

%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title