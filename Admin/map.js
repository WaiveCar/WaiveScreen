import Map from 'ol/Map.js';
import View from 'ol/View.js';
import {Draw, Modify, Snap} from 'ol/interaction.js';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer.js';
import {OSM, Vector as VectorSource} from 'ol/source.js';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style.js';
import {fromLonLat, toLonLat} from 'ol/proj';
import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import Circle from 'ol/geom/Circle';

var raster = new TileLayer({
  source: new OSM()
});

var source = new VectorSource();
var vector = new VectorLayer({
  source: source,
  style: new Style({
    fill: new Fill({
      color: 'rgba(255, 255, 255, 0.4)'
    }),
    stroke: new Stroke({
      color: '#000000',
      width: 2
    }),
    image: new CircleStyle({
      radius: 7,
      fill: new Fill({
        color: '#ffcc33'
      })
    })
  })
});

// eventually use geoip
var map = new Map({
  layers: [raster, vector],
  target: 'map',
  view: new View({
    center: fromLonLat([-118.3, 34.02]),
    zoom: 13
  })
});

var modify = new Modify({source: source});
map.addInteraction(modify);

var draw, snap; // global so we can remove them later
var typeSelect = document.getElementById('type');

function addInteractions() {
  draw = new Draw({
    source: source,
    type: typeSelect.value
  });
  map.addInteraction(draw);
  snap = new Snap({source: source});
  map.addInteraction(snap);

}
function getShapes() {
  let shapes = vector.getSource().getFeatures().map(row => {
    var kind = row.getGeometry();
    if (kind instanceof Polygon) {
      return ['Polygon', kind.getCoordinates()[0].map(coor => toLonLat(coor))];
    } else {
      return ['Circle', toLonLat(kind.getCenter()), kind.getRadius()];
    }
  });

  return shapes;
}

function drawShapes(list) {
  list.forEach(shape => {
    var feature;
    if(shape[0] === 'Circle') {
      feature = new Feature({
        geometry: new Circle(fromLonLat(shape[1]), shape[2])
      });
    }
    else if(shape[0] === 'Polygon') {
      feature = new Feature({
        geometry: new Polygon([shape[1].map(coor => fromLonLat(coor))])
      });
    }
    vector.getSource().addFeature(feature);
  });
}

self.save = function() {
  localStorage['shapes'] = JSON.stringify(getShapes());
}

self.load = function() {
  let shapes = JSON.parse(localStorage['shapes']);
  drawShapes(shapes);
}

window.onkeyup = function(e) {
  if(e.key === 'Delete') {
    draw.removeLastPoint();
  }
  if(e.key === 'Escape') {
    let shapeList = vector.getSource().getFeatures();
    if(shapeList) {
      vector.getSource().removeFeature(shapeList.slice(-1)[0]);
    }
  }
}
typeSelect.onchange = function() {
  map.removeInteraction(draw);
  map.removeInteraction(snap);
  addInteractions();
};

addInteractions();
