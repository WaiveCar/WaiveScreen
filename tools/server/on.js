#!/usr/bin/node
const { Client } = require('tplink-smarthome-api');

const client = new Client();

client.on('plug-new', function (plug) {
  plug.setPowerState(true);
  setTimeout(function(){
    process.exit();
  }, 1000);
});

client.startDiscovery().on('device-new', (device) => {
  device.setPowerState(true);
});


