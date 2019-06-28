function change(id, what) {
  var newval = prompt(`Change the ${what}`)
  if(newval) {
    fetch(new Request('/api/screens', {
      method: 'POST', 
      body: JSON.stringify({id: id, [what]: newval})
    })).then(res => {
      console.log('success', res);
    });
  }
}

