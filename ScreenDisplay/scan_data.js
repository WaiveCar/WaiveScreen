function loadScanDataInto(targetId) {
  var evtSource = new EventSource("http://localhost:9998", { withCredentials: false } );

  evtSource.onopen = function(event) {
    document.getElementById(targetId).parentElement.style.display = 'block';
  }
  evtSource.onerror = function(event) {
    document.getElementById(targetId).parentElement.style.display = 'none';
  }

  evtSource.onmessage = function(event) {
    //console.log(event.data);
    const curUl = document.getElementById(targetId);
    const newUl = document.createElement("ul");
    newUl.id = targetId;
    const deviceList = JSON.parse(event.data);
    for ( const device of deviceList.values() ) {
      const newLi = document.createElement("li");
      newLi.innerHTML = device.mac_addr + " " + device.cur_rssi + "dBm"
      newUl.appendChild(newLi);
    }
    //newElement.innerHTML = "message: " + event.data;
    curUl.replaceWith(newUl);
  }
}

loadScanDataInto('scanData');
