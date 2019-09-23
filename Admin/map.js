import Map from 'ol/Map.js';
import View from 'ol/View.js';
import {GeoJSON} from 'ol/format';
import {Draw, Modify, Snap} from 'ol/interaction.js';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer.js';
import {OSM, Cluster, Vector as VectorSource} from 'ol/source.js';
import {Circle as CircleStyle, Icon, Fill, Stroke, Style, Text} from 'ol/style.js';
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
    draw: true,
    select: false,
  }, opts || {});

  var raster = new TileLayer({
    source: new OSM()
  });

  var _draw, _snap;
  var source = {};
  var dom = document.getElementById(opts.target);
	var styleCache = {
    car: new Style({
      image: new Icon({
        src: '/Admin/car.png'
      })
    }),
    screen: new Style({
      image: new Icon({
        src: '/Admin/screen.png'
      })
    })
  };

  var _layers = [raster];

  // points {
  if(opts.points) {
    var featureMap = opts.points.filter(row => row.lng).map(row => {
      return {
        type: "Feature",
        properties: {
          icon: row.is_fake ? 'screen' : 'car'
        },
        geometry: {
          type: "Point",
          coordinates: fromLonLat([row.lng, row.lat])
        }
      };
    });
    featureMap = {type: "FeatureCollection", features: featureMap};

    source.screen = new VectorSource({
      format: new GeoJSON(),
      loader: function() {
        source.screen.addFeatures(
          source.screen.getFormat().readFeatures(JSON.stringify(featureMap))
        );
      }
    });

    // clustering {
    var clusterSource = new Cluster({
      distance: 55,
      source: source.screen
    });

    var clusters = new VectorLayer({
      source: clusterSource,
      style: function(obj) {
        var features = obj.get('features');
   			var size = features.length;
        if(size > 1) {
          var style = styleCache[size];
          if (!style) {
            style = new Style({
              image: new CircleStyle({
                radius: 14,
                fill: new Fill({
                  color: '#000'
                })
              }),
              text: new Text({
                text: size.toString(),
                fill: new Fill({
                  color: '#fff'
                })
              })
            });
            styleCache[size] = style;
          }
          return style;
        } else {
          return styleCache[features[0].getProperties().icon];
        }
      }
		});
	
    _layers.push(clusters);
    // } clustering

    //_layers.push(points);
  }
  // } points

  // drawlayer {
  if(opts.draw) {
    var typeSelect = document.getElementById(opts.typeSelect);
    source.draw = new VectorSource();
    var modify = new Modify({source: source.draw});
    var draw = new VectorLayer({
      source: source.draw,
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
    function addInteractions() {
      _draw = new Draw({
        source: source.draw,
        type: typeSelect.value
      });
      _map.addInteraction(_draw);
      _snap = new Snap({source: source.draw});
      _map.addInteraction(_snap);
    }
    function getShapes() {
      let shapes = draw.getSource().getFeatures().map(row => {
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
        draw.getSource().addFeature(feature);
      });
    }

    function clear() {
      for(var feature of draw.getSource().getFeatures()) {
        draw.getSource().removeFeature(feature);
      }
    }
    function removeShape() {
      let shapeList = draw.getSource().getFeatures();
      if(shapeList) {
        draw.getSource().removeFeature(shapeList.slice(-1)[0]);
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
  }
  // } drawlayer

  _layers.push(draw);

  // eventually use geoip
  var _map = new Map({
    layers: _layers,
    target: opts.target,
    view: new View({
      center: fromLonLat(opts.center),
      zoom: opts.zoom
    })
  });

  if(opts.draw) {
    _map.addInteraction(modify);
  }

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
