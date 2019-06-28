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

