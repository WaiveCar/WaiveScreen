import Map from 'ol/Map.js';
import View from 'ol/View.js';
import {GeoJSON} from 'ol/format';
import {Draw, Modify, Snap} from 'ol/interaction.js';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer.js';
import {OSM, Vector as VectorSource} from 'ol/source.js';
import {Circle as CircleStyle, Icon, Fill, Stroke, Style} from 'ol/style.js';
import {fromLonLat, toLonLat} from 'ol/proj';
import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import Circle from 'ol/geom/Circle';
import {bbox} from 'ol/loadingstrategy';

window.map = function(opts) {
  //
  // opts:
  //  target: the dom id to draw the map to.
  //  center: the center of the map in lon/lat
  //
  // func:
  //  clear() - remove all the shapes
  //  

  opts = Object.assign({}, {
    target: 'map',
    center: [-118.3, 34.02],
    zoom: 13,
    typeSelect: 'type',
  }, opts || {});

  var raster = new TileLayer({
    source: new OSM()
  });

  var _draw, _snap;
  var dom = document.getElementById(opts.target);
  var typeSelect = document.getElementById(opts.typeSelect);

  var source = new VectorSource();
  var modify = new Modify({source: source});
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

  var _layers = [raster, vector];

  if(opts.points) {
    var featureMap = opts.points.filter(row => row.lng).map(row => {
      return {
        "type": "Feature",
        properties: {},
        "geometry": {
          "type": "Point",
          "coordinates": fromLonLat([row.lng, row.lat])
        }
      };
    });
    featureMap = {type: "FeatureCollection", features: featureMap};
    console.log(featureMap);

    function styleFunction() {
      return new Style({
        image: new Icon({
          src: '/car.png'
        })
      })
    }

    var source = new VectorSource({
      format: new GeoJSON(),
      strategy: bbox,
      loader: function() {
        self.p = source;
        source.addFeatures(
          source.getFormat().readFeatures(JSON.stringify(featureMap))
        );
      }
    });

    var points = new VectorLayer({
      source: source,
      style: styleFunction
    });
    _layers.push(points);
  }

  // eventually use geoip
  var _map = new Map({
    layers: _layers,
    target: opts.target,
    view: new View({
      center: fromLonLat(opts.center),
      zoom: opts.zoom
    })
  });

  _map.addInteraction(modify);

  function addInteractions() {
    _draw = new Draw({
      source: source,
      type: typeSelect.value
    });
    _map.addInteraction(_draw);
    _snap = new Snap({source: source});
    _map.addInteraction(_snap);
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
    clear();
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

  function clear() {
    for(var feature of vector.getSource().getFeatures()) {
      vector.getSource().removeFeature(feature);
    }
  }
  function removeShape() {
    let shapeList = vector.getSource().getFeatures();
    if(shapeList) {
      vector.getSource().removeFeature(shapeList.slice(-1)[0]);
    }
  }
  function removePoint() {
    _draw.removeLastPoint();
  }

  dom.onkeyup = function(e) {
    if(e.key === 'Delete') { removePoint(); }
    if(e.key === 'Backspace') { removeShape(); }
  }

  typeSelect.onchange = function() {
    _map.removeInteraction(_draw);
    _map.removeInteraction(_snap);
    addInteractions();
  };

  addInteractions();

  return {
    _map: _map,
    center: function(coor, zoom) {
      _map.getView().setCenter(fromLonLat(coor));
      if(zoom) {
        _map.getView().setZoom(zoom);
      }
    },
    removeShape: removeShape,
    removePoint: removePoint,
    save: getShapes,
    load: drawShapes,
    clear: clear
  };
}
