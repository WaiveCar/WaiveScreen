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

function command(id) {
  var cmd = prompt(`Give a command for ${id}`);
  if(cmd) {
    let parts = cmd.split(' ');
    fetch(new Request('/api/commands', {
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
      dom.innerHTML = res[what];
    });
  }
}

