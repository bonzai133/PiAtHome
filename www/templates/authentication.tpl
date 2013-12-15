%def rightblock():
	<span id="userName"></span>
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