%def rightblock():
	<h1>Historique des erreurs</h1>

    <table id="list_errors"></table>
    <div id="pager_errors"></div>

%end

%def jscript():
<script>
	$(document).ready( function() {

	    $(function () {
	        $("#list_errors").jqGrid({
	            url: "/list_errors_grid.json",
	            datatype: "json",
	            mtype: "GET",
	            colNames: ["Date", "Code", "Description"],
	            colModel: [
	                { name: "datetime", width: 150 },
	                { name: "errCode", width: 55 },
	                { name: "desc", width: 400},
	            ],
	            pager: "#pager_errors",
	            rowNum: 10,
	            rowList: [10, 20, 30, 50, 100],
	            sortname: "datetime",
	            sortorder: "desc",
	            viewrecords: true,
	            gridview: true,
	            autoencode: true,
	            height: "100%",
	            caption: "Liste des erreurs"
	        }); 
	    });     
	    
	});


</script>
%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title