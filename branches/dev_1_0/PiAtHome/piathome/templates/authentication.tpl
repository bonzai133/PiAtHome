%def rightblock():
	<span id="userName"></span>
    % if not isAuthentic:
	<form action="/login" method="POST">
	    <table>
	        <tr>
	            <td><label for="UserName">User name</label></td>
	            <td><input id="UserName" name="UserName" type="text"></td>
	        </tr>
	        <tr>
	            <td><label for="Password">Password</label></td>
	            <td><input id="Password" name="Password" type="password"></td>
	        </tr>
	    </table>
	    <input id='btnLogout' type='button' value='Log out' disabled/>
	    <input type='submit' value='Log in'/>
	</form>
	% else:
    <form action="/login" method="POST">
        <input id='btnLogout' type='button' value='Log out' disabled/>
    </form>	
    % end

	% if isAdmin:
	    <div style="border:2px solid;border-radius:12px;padding:10px;">
		    <form action="/createUser" method="POST">
		        <table>
		            <tr>
		                <td><label for="UserName">User name</label></td>
		                <td><input id="UserName" name="UserName" type="text"></td>
		            </tr>
                    <tr>
                        <td><label for="RealName">Nom affiché</label></td>
                        <td><input id="RealName" name="RealName" type="text"></td>
                    </tr>		            <tr>
		                <td><label for="Password">Password</label></td>
		                <td><input id="Password" name="Password" type="password"></td>
		            </tr>
		        </table>
		        <input type='submit' value='Create User'/>
		    </form>	    
	    </div>
	% end

    
%end

%def jscript():
    <script type="text/javascript">
        $(function () {
            $.ajax({
                url: "/getUser",
                cache: false,
                success: function(data) {
                    if (data.user)
                    {
                        $('#userName').text(data.user);
                        $('#btnLogout').removeAttr('disabled');
                        $('#btnLogout').click(function() {
                            $.post('/logout', null, function() {
                                location.reload();
                            });
                        });
                    }
                    else
                    {
                        $('#userName').text("Vous n'êtes pas identifié");
                    }
                }
            });
            });
    </script>


%end



%rebase columns rightblock=rightblock, jscript=jscript, title=title, login=login