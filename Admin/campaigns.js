var _id, _campaign;
$(function() {
  $("#editModal").on('shown.bs.modal', function() {
    if(!self._map){ 
      self._map = map({points:Screens});
    }
    let success = false;
    _campaign = get(_id);
    if(_campaign.shape_list) {
      let first = _campaign.shape_list[0];

      if(first[0] === 'Circle') {
        _map.center(first[1]);
        success = true;
      } else if(first[0] === 'Polygon') {
        _map.center(first[1][0]);
        success = true;
      }
    }

    if(success) {
      _map.load(_campaign.shape_list);
    } else {
      _map.center([-118.34,34.06], 11);
    }
  });
});

function clearmap() {
  _map.clear();
}

function geofence(id){
  _id = id;
  $("#editModal").modal();
}

function removeShape() {
  _map.removeShape();
}

function change_time(id, current) {
  var newValStr = prompt("Change to what value?", current), 
      newValNum;

  if(!newValStr) {
    return show("Canceled");
  }

  newValNum = parseInt(newValStr, 10);
  if(isNaN(newValNum)) {
    show(newValStr + " is not a number");
  } else {
    post('campaign_update', {id: id, duration_seconds: newValNum}, res => {
      show({data: 'Updated Campaign'}, 1000);
    });
  }
}

function create_campaign() {
  post('campaign', {}, res => {
    show({data: 'Created Campaign'}, 1000);
  });
}

function geosave() {
  var coords = _map.save();
  // If we click on the map again we should show the updated coords
  _campaign.shape_list = coords;
  post('campaign_update', {id: _id, geofence: coords}, res => {
    $("#editModal").modal('hide');
    show({data: 'Updated Campaign'}, 1000);
  });
}

