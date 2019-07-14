function get(id) {
  var res = Data.filter(row => row.id == id);
  return res ? res[0] : null;
}
function show(res) {
  let notice = document.getElementById('notice');
  notice.innerHTML = res.data || "OK";
  notice.style.display = 'block';
  setTimeout(function() {
    notice.style.display = 'none';
  }, 4000);
}

function change(id, what, el) {
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
