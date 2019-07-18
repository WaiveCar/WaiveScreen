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

  notice.innerHTML = res.data || "OK";
  notice.style.display = 'block';
  setTimeout(function() {
    notice.style.display = 'none';
  }, timeout);
}

function change(id, what, el) {
  post('screens', {id: id, [what]: el.value}, res => {
    show({data: 'Updated project'}, 1000);
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

function edit(id) {
  var screen = get(id);
  $("#ModalLabel").html(screen.uid);
  $("#editModal").modal();
}

$(function() {
  if(document.getElementById('dataTable')) {
    $('#dataTable').DataTable({
      stateSave: true,
      order: [[10, 'desc']]
    });
  } else {
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
    update_campaign($(e.target).data('campaign'), e.target);
  });
});


function update_campaign(campaign, el) {
  // Before the payment is processed by paypal, a user's purchase is sent to the server with 
  // the information that has so far been obtained including the picture.
  let formData = new FormData();

  formData.append('campaign_id', campaign);
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
