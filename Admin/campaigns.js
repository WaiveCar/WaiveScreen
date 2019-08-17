var _id, _campaign;
$(function() {
  $("#editModal").on('shown.bs.modal', function() {
    if(!self._map){ 
      self._map = map();
    }
    _campaign = get(_id);
    if(_campaign.shape_list) {
      let first = _campaign.shape_list[0];
      if(first[0] === 'Circle') {
        _map.center(first[1]);
      } else {
        _map.center(first[1][0]);
      }
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

function geosave() {
  var coords = _map.save();
  // If we click on the map again we should show the updated coords
  _campaign.shape_list = coords;
  post('campaign_update', {id: _id, geofence: coords}, res => {
    $("#editModal").modal('hide');
    show({data: 'Updated Campaign'}, 1000);
  });
}

