window.onload = function init() {
  self.ads = Engine({
    server: 'http://localhost:4096/'
  });

  ads.on('system', function(data) {
    document.getElementsByClassName('info')[0].innerHTML = [data.number.slice(-7), data.uuid.slice(0,5)].join(' ');
  });

  ads.Start();

  function doWs() { 
    var ws = new WebSocket("ws://127.0.0.1:4096/ws");

    ws.onerror = ws.onclose = function(){ 
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
      }
      if(payload.action === 'eval') {
        eval(payload.args);
      }
      if(payload.action === 'playnow') {
        let job = ads.AddJob(payload.args);//, {priority: ads.Get('maxPriority') + 1});
        ads.PlayNow(job);
      }

      console.log(event.data);
    };
  }
}
