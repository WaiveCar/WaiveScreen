#!/usr/bin/nodejs
const { Client } = require('tplink-smarthome-api');
let fs = require('fs');

const client = new Client();

client.on('plug-new', function (plug) {
  function reader() {
    plug.emeter.getRealtime().then((opts) => {
      delete opts['voltage'];
      console.log( Object.values(opts).join(' ') );
      setTimeout(reader, 750);
    });
  }
  reader();
});

// Look for devices, log to console, and turn them on
client.startDiscovery().on('device-new', (device) => {
  device.setPowerState(true);
});


