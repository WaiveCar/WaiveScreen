#!/usr/bin/node
const { Client } = require('tplink-smarthome-api');

const client = new Client();

client.startDiscovery().on('device-new', (device) => {
  device.setPowerState(false);
  setTimeout(function(){
    process.exit();
  }, 1000);
});


