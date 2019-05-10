#!/usr/bin/node
const { Client } = require('tplink-smarthome-api');

const client = new Client();

client.on('plug-new', function (plug) {
  console.log("off");
  plug.setPowerState(false);
  setTimeout(function(){
    console.log("on");
    plug.setPowerState(true);
    setTimeout(function(){
      console.log("exit");
      process.exit();
    }, 4500);
  }, 4500);
});

client.startDiscovery().on('device-new', (device) => {
  device.setPowerState(true);
});


