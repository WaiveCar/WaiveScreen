function tableIt(table, opts) {
  opts = Object.assign({
    filter: (opts && opts.filter || []).concat(['id','password','created_at','image'])
  }, opts || {});

  $.getJSON(`/api/${table}`, function(res) {
    let fields = Object.keys(res[0]).filter(row => !opts.filter.includes(row)) 
    $("#table-head").html(
      "<tr>" +
      fields.map(field => `<th scope="col">${field}</th>`) +
      "</tr>"
    );
    $("#table-body").html(
      res.map(function(row) {
        return '<tr>' +
          fields.map(function(field) {
            return field === 'name' ?
              `<td><a href="/${table}/${row.id}">${row[field]}</a></td>` :
              `<td>${row[field]}</td>` ;
          }) + '</tr>'
      })
    )
  });
}

