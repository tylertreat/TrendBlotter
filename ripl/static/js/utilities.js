/* global $, Backbone, _, Handlebars */

var ripl = ripl || {};
ripl.utilities = (function($, Backbone, _, Handlebars) {
    "use strict";

    var instance = {};

    // Use this to cache each template that gets loaded from the server.
    instance.templates = {},

    instance.getTemplate = function(id, callback) {

        // Check if the template is cached.
        if (instance.templates[id]) {
            return callback(instance.templates[id]);
        }

        // Load the template otherwise.
        var
            url = '/static/templates/' + id + '.html',

        // Use Traffic Cop to handle marshalling requests to the server. 
            promise = $.trafficCop(url);

        // Wire up a handler for this request via jQuery's promise API.
        promise.done(function(template) {
            var tmp = Handlebars.compile(template);
            instance.templates[id] = tmp;
            callback(tmp);
        });
    }   

    return instance;

}($, Backbone, _, Handlebars));
