window.onload = function init() {
  self.ads = Engine({
    server: 'http://localhost:4096/'
  });

  ads.on('system', function(data) {
    document.getElementsByClassName('info')[0].innerHTML = [data.number.slice(-7), data.uuid.slice(0,5)].join(' ');
  });

  ads.Start();

  var ws = new WebSocket("ws://127.0.0.1:4096/ws");
  ws.onmessage = function(event) {
    console.log(event.data);
  });
}
