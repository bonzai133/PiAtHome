%def rightblock():
	<h1>Historique des erreurs</h1>

    <div id="div_errors"></div>

	
%end

%def jscript():
<script>
	$(document).ready( function() {

	    function updateErrors() {
	        //Get errors
	        $.getJSON("/list_errors.json",function(data) {
	       		$.each(data.errors, function(i,data) {
		       		var div_data =
		       		"<div>"+ data.date + " | " + data.code + " | " + data.desc + "</div>";
		       		$(div_data).appendTo("#div_errors");
		       	});
	       	});
	    }
	    
	    updateErrors();
	});
</script>
%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title