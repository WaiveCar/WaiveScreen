var _append = false,
    _screen = false;

function get(id) {
  var res = Data.filter(row => row.id == id);
  return res ? res[0] : null;
}

function post(ep, body, cb) {
  fetch(new Request(`/api/${ep}`, {
    method: 'POST', 
    body: JSON.stringify(body)
  })).then(res => {
    if (res.status === 200) {
      return res.json();
    }
  }).then(cb);
}

function show(res, timeout) {
  let notice = document.getElementById('notice');
  timeout = timeout || 4000;
  if(res.res || !('res' in res)) {
    notice.className = 'alert alert-primary';
  } else {
    notice.className = 'alert alert-danger';
  }
  if('data' in res) {
    notice.innerHTML = res.data || 'OK';
  } else {
    notice.innerHTML = res;
  }
  notice.style.display = 'block';
  setTimeout(function() {
    notice.style.display = 'none';
  }, timeout);
}

function change(id, what, el) {
  post('screens', {id: id, [what]: el.value}, res => {
    show({data: 'Updated screen'}, 1000);
  });
}

function promptchange(id, what, el) {
  let dom = el.parentNode.firstElementChild;
  var newval = prompt(`Change the ${what}`, dom.innerHTML)
  if(newval !== null) {
    dom.innerHTML = '&#8987;...';
    post('screens', {id: id, [what]: newval}, res => {
      dom.innerHTML = res[what];
    });
  }
}

function scope_command() {
  var payload = {};
  ['field','value','command','args'].forEach(row => {
    payload[row] =  document.getElementById(row).value;
  });
  post('command', payload, show);
}

function command(id, name) {
  name = name || id;
  var cmd = prompt(`Give a command for ${name}`);
  if(cmd) {
    let parts = cmd.split(' ');
    post('command', {
      field: 'id',
      value: id,
      command: parts[0], 
      args: parts.slice(1).join(' ')
    }, show);
  }
}

function obj2span(obj) {
  var out = [];
  for(var key in obj) {
    out.push(`<span>${key}</span><span>${obj[key]}</span>`);
  }
  return '<div>' + out.join('</div><div>') + '</div>';
}

function remove() {
  if(confirm(`Are you sure you want to remove ${_screen.uid}?`)) {
    post('screens', {id: _screen.id, removed: true }, res => {
      show({data: 'Updated screen'}, 1000);
    });
    $("#editModal").modal('hide');
  }
}

function edit(id) {
  var screen = get(id);
  var keylist = ['last_seen','ignition_time','ignition_state','expected_hour','imei','pings','last_task'];
  var out = keylist.map(row => screen[row] ? 
    `<span>${row}</span><span>${JSON.stringify(screen[row]).replace(/\"/g,'')}</span>`:
    `<span>${row}</span><span>&mdash;</span>`
  );
  out.push(`<span>features</span><span>${obj2span(screen.features)}</span>`); 
  out.unshift(`<span>Now</span><span>${now}</span>`); 
  
  _screen = screen;

  $("#editModal .modal-body").html('<div>' + out.join('</div><div>') + '</div>');
  $("#ModalLabel").html(screen.uid);
  $("#editModal").modal();
}

$(function() {
  if(document.getElementById('dataTable')) {
    $('#dataTable').DataTable({
      stateSave: true,
      order: [[10, 'desc']]
    });
  } else if(self.Data){
    for (var which of Data) {
      let id = which.id;
      let engine = Engine({
        container: document.getElementById(`asset-container-${id}`),
        target: { width: width, height: height }
      });
      engine.AddJob(which);
      engine.Start();
    }
  }
  $('.form-control-file').on('change', function(e) {
    let uploadInput = e.target;
    update_campaign_files($(e.target).data('campaign'), e.target);
  });
});


function append() {
  _append = true;
}

function update_campaign(obj) {
  return axios({
    method: 'post',
    url: '/api/campaign_update',
    data: obj
  }).then(function(resp) {
    show("Updated campaign");
  });
}

function update_campaign_files(campaign, el) {
  // Before the payment is processed by paypal, a user's purchase is sent to the server with 
  // the information that has so far been obtained including the picture.
  let formData = new FormData();

  formData.append('campaign_id', campaign);
  if(_append) { 
    formData.append('append', '1');
    _append = false;
  }
  for(var ix = 0; ix < el.files.length; ix++) {
    formData.append('file' + ix, el.files[ix]);
  }

  return axios({
    method: 'post',
    url: '/api/campaign_update',
    data: formData,
    config: {
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  }).then(function(resp) {
    show("Updated assets");
  });
}
