function get(id) {
  var res = Data.filter(row => row.id == id);
  return res ? res[0] : null;
}
function show(res, timeout) {
  let notice = document.getElementById('notice');
  timeout = timeout || 4000;
  notice.innerHTML = res.data || "OK";
  notice.style.display = 'block';
  setTimeout(function() {
    notice.style.display = 'none';
  }, timeout);
}

function change(id, what, el) {
  fetch(new Request('/api/screens', {
    method: 'POST', 
    body: JSON.stringify({id: id, [what]: el.value})
  })).then(res => {
    if (res.status === 200) {
      return res.json();
    }
  }).then(res => {
    show({data: 'Updated project'}, 1000);
  });
}

function promptchange(id, what, el) {
  let dom = el.parentNode.firstElementChild;
  var newval = prompt(`Change the ${what}`, dom.innerHTML)
  if(newval !== null) {
    dom.innerHTML = '&#8987;...';
    fetch(new Request('/api/screens', {
      method: 'POST', 
      body: JSON.stringify({id: id, [what]: newval})
    })).then(res => {
      if (res.status === 200) {
        return res.json();
      }
    }).then(res => {
      dom.innerHTML = res[what];
    });
  }
}

function command(id, name) {
  name = name || id;
  var cmd = prompt(`Give a command for ${name}`);
  if(cmd) {
    let parts = cmd.split(' ');
    fetch(new Request('/api/command', {
      method: 'POST', 
      body: JSON.stringify({
        id: id, 
        cmd: parts[0], 
        args: parts.slice(1).join(' ')
      })
    })).then(res => {
      if (res.status === 200) {
        return res.json();
      }
    }).then(res => {
      show(res);
    });
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
