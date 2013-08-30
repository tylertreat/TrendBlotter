require.config({
    paths: {
        jquery: 'lib/jquery-1.9.1.min',
        underscore: 'lib/underscore-min',
        backbone: 'lib/backbone-min',
        bootstrap: 'lib/bootstrap-2.3.2',
    },
    shim: {
        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        underscore: {
            exports: '_'
        }, 
        bootstrap: {
            deps: ["jquery"],
            exports: 'bootstrap'
        }
    }
});

require([
    'jquery',
    'underscore',
    'backbone',
    'bootstrap',
], function($, _, Backbone, Bootstrap){
    // App initialization logic here
});
