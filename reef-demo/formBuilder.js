function ucfirst(what) {

  return what ? what[0].toUpperCase() + what.slice(1) : what;
}
function select(what, data) {
  function gen(res) {
    let options = res.map(
      row => `<option value=${row.id}>${row.name}</option>`,
    ), name = what;
    if (!data) {
      options.unshift("<option value=''>-- None --</option>");
      name += "_id";
    } 

    document.getElementById(`${what}-wrap`).innerHTML = `
          <select class="form-control" name="${name}">
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
    $.getJSON(`http://192.168.86.58/api/${what}s`, gen);
  }
}

function doit(table, opts) {
  opts = opts || {};
  opts = Object.assign({
    fields: {},
    container: 'createForm',
    name: ucfirst(table || '')
  }, opts);
  opts.hide = ['id', 'image', 'created_at'].concat(opts.hide);

  var 
    wordMap = {org: 'organization'},
    typeMap = {password: 'password'},
    form = document.getElementById(opts.container);

  $('.head').each(function(k, j) {
    j.innerHTML = `New ${opts.name}`;
  });

  form.setAttribute('action', `http://192.168.86.58/api/${table}s?next=/${table}s`);

  function builder(schema) {
    var html = [],
      type,
      input,
      xref,
      name;

    for (var k in schema) {
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
      name = ucfirst(wordMap[name] || name);

      html.push(`
            <div class="form-group">
              <label for="${k}">${name}</label>
              ${input}
            </div>
          `);
    }
    if(table) {
      html.push(
        `<button type="submit" class="btn btn-primary">Create ${opts.name}</button>`,
      );
    }
    form.innerHTML = html.join('');
  }

  if(opts.schema) {
    builder(opts.schema);
  } else {
    $.getJSON(`http://192.168.86.58/api/schema?table=${table}`, builder);
  }
}
