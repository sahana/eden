/**
 * Class: OpenLayers.Strategy.AttributeCluster
 * Strategy for vector feature clustering based on feature attributes.
 *
 * Inherits from:
 *  - <OpenLayers.Strategy.Cluster>
 */
OpenLayers.Strategy.AttributeCluster = OpenLayers.Class(OpenLayers.Strategy.Cluster, {
    /**
     * the attribute to use for comparison
     */
    attribute: null,
    /**
     * Method: shouldCluster
     * Determine whether to include a feature in a given cluster.
     *
     * Parameters:
     * cluster - {<OpenLayers.Feature.Vector>} A cluster.
     * feature - {<OpenLayers.Feature.Vector>} A feature.
     *
     * Returns:
     * {Boolean} The feature should be included in the cluster.
     */
    shouldCluster: function(cluster, feature) {
        var cc_attrval = cluster.cluster[0].attributes[this.attribute];
        var fc_attrval = feature.attributes[this.attribute];
        var superProto = OpenLayers.Strategy.Cluster.prototype;
        return cc_attrval === fc_attrval && 
               superProto.shouldCluster.apply(this, arguments);
    },
    CLASS_NAME: "OpenLayers.Strategy.AttributeCluster"
});

/**
 * Class: OpenLayers.Strategy.AttributeClusterMultiple
 * Strategy for vector feature clustering based on feature attributes.
 * Clusters across multiple layers
 *
 * Inherits from:
 *  - <OpenLayers.Strategy.AttributeCluster>
 */
OpenLayers.Strategy.AttributeClusterMultiple = OpenLayers.Class(OpenLayers.Strategy.AttributeCluster, {
    /**
     * Property: clusterLayer
     * {<OpenLayers.Layer.Vector>} The layer the clusters render on
     */
    clusterLayer: null,

    /**
     * Property: layers
     * {Array(<OpenLayers.Layer.Vector>)} The layers this strategy belongs to.
     */
    layers: null,

    /**
     * Constructor: OpenLayers.Strategy
     * Abstract class for vector strategies.  Create instances of a subclass.
     *
     * Parameters:
     * options - {Object} Optional object whose properties will be set on the
     *     instance.
     */
    initialize: function(options) {
        OpenLayers.Util.extend(this, options);
        this.options = options;
        // set the active property here, so that user cannot override it
        this.active = false;
        // Initialize the layer which holds the clusters
        this.clusterLayer = new OpenLayers.Layer.Vector('Clusters', {
            displayInLayerSwitcher: false
        });
    },

    /**
     * APIMethod: destroy
     * Clean up the strategy.
     */
    destroy: function() {
        this.deactivate();
        this.clusterLayer = null;
        this.layers = null;
        this.options = null;
    },

    /**
     * Method: setLayer
     * Called to update the <layers> property.
     *
     * Parameters:
     * layer - {<OpenLayers.Layer.Vector>}
     */
    setLayer: function(layer) {
        var found = false;
        var layers = this.layers;
        if (layers) {
            for (var i=0; i<layers.length; ++i) {
                if (layers[i] == layer) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                layers.push(layer);
            }
        } else {
            layers = [layer];
        }
    },

    /**
     * APIMethod: activate
     * Activate the strategy.  Register any listeners, do appropriate setup.
     * 
     * Returns:
     * {Boolean} The strategy was successfully activated.
     */
    activate: function() {
        var activated = OpenLayers.Strategy.prototype.activate.call(this);
        if (activated) {
            var layers = this.layers;
            if (layers) {
                for (var i=0; i<layers.length; ++i) {
                    layers[i].events.on({
                        "beforefeaturesadded": this.cacheFeatures,
                        "featuresremoved": this.clearCache,
                        "moveend": this.cluster,
                        scope: this
                    });
                }
            }
        }
        return activated;
    },

    /**
     * APIMethod: deactivate
     * Deactivate the strategy.  Unregister any listeners, do appropriate
     *     tear-down.
     * 
     * Returns:
     * {Boolean} The strategy was successfully deactivated.
     */
    deactivate: function() {
        var deactivated = OpenLayers.Strategy.prototype.deactivate.call(this);
        if (deactivated) {
            this.clearCache();
            var layers = this.layers;
            if (layers) {
                for (var i=0; i<layers.length; ++i) {
                    layers[i].events.un({
                        "beforefeaturesadded": this.cacheFeatures,
                        "featuresremoved": this.clearCache,
                        "moveend": this.cluster,
                        scope: this
                    });
                }
            }
        }
        return deactivated;
    },

    /**
     * Method: cluster
     * Cluster features based on some threshold distance.
     *
     * Parameters:
     * event - {Object} The event received when cluster is called as a
     *     result of a moveend event.
     */
    cluster: function(event) {
        if ((!event || event.zoomChanged) && this.features) {
            var layers = this.layers;
            var resolution = layers[0].map.getResolution();
            if (resolution != this.resolution || !this.clustersExist()) {
                this.resolution = resolution;
                var clusters = [];
                var feature, clustered, cluster;
                for (var i=0; i<this.features.length; ++i) {
                    feature = this.features[i];
                    if (feature.geometry) {
                        clustered = false;
                        for (var j=clusters.length-1; j>=0; --j) {
                            cluster = clusters[j];
                            if (this.shouldCluster(cluster, feature)) {
                                this.addToCluster(cluster, feature);
                                clustered = true;
                                break;
                            }
                        }
                        if (!clustered) {
                            clusters.push(this.createCluster(this.features[i]));
                        }
                    }
                }
                this.clustering = true;
                for (var i=0; i<layers.length; ++i) {
                    layers[i].removeAllFeatures();
                }
                this.clusterLayer.removeAllFeatures();
                this.clustering = false;
                if (clusters.length > 0) {
                    if (this.threshold > 1) {
                        var clone = clusters.slice();
                        clusters = [];
                        var candidate;
                        for (var i=0, len=clone.length; i<len; ++i) {
                            candidate = clone[i];
                            if (candidate.attributes.count < this.threshold) {
                                Array.prototype.push.apply(clusters, candidate.cluster);
                            } else {
                                clusters.push(candidate);
                            }
                        }
                    }
                    this.clustering = true;
                    // A legitimate feature addition could occur during this
                    // addFeatures call.  For clustering to behave well, features
                    // should be removed from a layer before requesting a new batch.
                    this.clusterLayer.addFeatures(clusters);
                    this.clustering = false;
                }
                this.clusters = clusters;
            }
        }
    },

    /**
     * Method: clustersExist
     * Determine whether calculated clusters are already on the layer.
     *
     * Returns:
     * {Boolean} The calculated clusters are already on the layer.
     */
    clustersExist: function() {
        var exist = false;
        var layers = this.layers;
        var features = [];
        for (var i=0; i<layers.length; ++i) {
            var lfeatures = layers[i].features;
            for (var i=0; i<lfeatures.length; ++i) {
                features.push(lfeatures[i])
            }
        }
        var clusters = this.clusters;
        if (clusters && clusters.length > 0 &&
           clusters.length == features.length) {
            exist = true;
            for (var i=0; i<clusters.length; ++i) {
                if (clusters[i] != features[i]) {
                    exist = false;
                    break;
                }
            }
        }
        return exist;
    },

    CLASS_NAME: "OpenLayers.Strategy.AttributeClusterMultiple"
});