token='123'
template = """"   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
   <script>
    var ip="";
    window.addEventListener('load',function () {
    $.getJSON("https://api.ipify.org?format=json",
                    function(data) {

      // Setting text of element P with id gfg
      location.replace("http:127.0.0.1:5000/track?token=%s?ip="+data.ip+"?data="+navigator.userAgent);
    })
   //location.replace("http:127.0.0.1:5000?ip="+ip);
     })
   </script>"""%(token)

with open('template.html','w') as htmlfile:
        htmlfile.write(template)
