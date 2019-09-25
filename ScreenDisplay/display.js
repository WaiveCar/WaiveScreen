function showText(what) {
  sms.innerHTML = what;
  sms.style.animationName = 'smsslide';

  setTimeout(function() {
    sms.style.animationName = 'none';
  }, 5100);
}

window.onload = function init() {
  self.ads = Engine({
    slowCPU: true,
    server: 'http://localhost:4096/'
  });
  //self.ads.Debug();

  self.sms = document.getElementById('sms');

  ads.on('system', function(data) {
    document.getElementsByClassName('info')[0].innerHTML = [data.number.slice(-7), data.uuid.slice(0,5)].join(' ');
  });

  ads.Start();

  function doIO() {
    var socket = io('http://localhost:5000');

    socket.on('engine', function(data) {
      ads[data.func](data.params);
    });
    socket.on('text', function(data) {
      showText(data.args);
    });
    socket.on('eval', function(data) {
      eval(data.args);
    });
    socket.on('playnow', function(data) {
      let job = ads.AddJob({url: data.args});
      ads.PlayNow(job);
    });
  }

  function doWS() { 
    var ws = new WebSocket("ws://127.0.0.1:4096/ws");

    ws.onerror = ws.onclose = function(){ 
      try {
        ws.close();
      } catch(ex) {}
      setTimeout(doWs, 1000);
    }

    ws.onmessage = function(event) {
      //
      // id: unique id
      // action: verb
      // args: noun
      //
      let payload = JSON.parse(event.data);

      if(payload.action === 'engine') {
        ads[payload.args.func](payload.args.params);
      } else if(payload.action === 'text') {
        showText(payload.args);
      } else if(payload.action === 'eval') {
        eval(payload.args);
      } else if(payload.action === 'playnow') {
        let job = ads.AddJob({url: payload.args});//, {priority: ads.Get('maxPriority') + 1});
        ads.PlayNow(job);
      }

      console.log(event.data);
    };
  }
  doWS();
}
