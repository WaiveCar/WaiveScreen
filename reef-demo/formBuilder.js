function ucfirst(what) {
  return what[0].toUpperCase() + what.slice(1);
}
function select(what, data) {
  function gen(res) {
    let options = res.map(
      row => `<option value=${row.id}>${row.name}</option>`,
    );
    if (!data) {
      options.unshift("<option value=''>-- None --</option>");
    }
    document.getElementById(`${what}-wrap`).innerHTML = `
          <select class="form-control" name="${what}_id">
            ${options}
          </select>
        `;
  }

  if (data) {
    // this needs to be done after it's in the dom so
    // we trick it.
    setTimeout(function() {
      gen(
        data.map(field => {
          return {id: field, name: field};
        }),
      );
    });
  } else {
    $.getJSON(`http://waivescreen.com/api/${what}s`, gen);
  }
}
function doit(table, opts) {
  var typeMap = {password: 'password'},
    form = document.getElementById('createForm'),
    obj = ucfirst(table);

  opts = opts || {};
  opts.fields = opts.fields || {};
  opts.hide = ['id', 'image', 'created_at'].concat(opts.hide);

  $('.head').each(function(k, j) {
    j.innerHTML = 'New ' + obj;
  });

  form.setAttribute('action', `/api/${table}s`);

  $.getJSON(`http://waivescreen.com/api/schema?table=${table}`, function(res) {
    var html = [],
      type,
      input,
      xref,
      name;

    for (var k in res) {
      if (opts.hide.includes(k)) {
        continue;
      }

      type = typeMap[k] || 'text';
      xref = k.match(/(\w*)_id/);

      if (xref) {
        let field = xref[1];
        name = field;
        input = `<div id=${field}-wrap></div>`;
        select(field);
      } else if (opts.fields[k]) {
        name = k;
        input = `<div id=${k}-wrap></div>`;
        select(k, opts.fields[k]);
      } else {
        name = k;
        input = `<input type="${type}" class="form-control" name="${k}">`;
      }

      name = ucfirst(name);

      html.push(`
            <div class="form-group">
              <label for="${k}">${name}</label>
              ${input}
            </div>
          `);
    }
    html.push(
      `<button type="submit" class="btn btn-primary">Create ${obj}</button>`,
    );
    document.getElementById('createForm').innerHTML = html.join('');
  });
}
