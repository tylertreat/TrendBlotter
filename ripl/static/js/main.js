require.config({
    paths: {
        jquery: 'lib/jquery-1.10.2.min',
        underscore: 'lib/underscore-min',
        backbone: 'lib/backbone-min'
    },
    shim: {
        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        underscore: {
            exports: '_'
        }
    }
});

require([
    'jquery',
    'underscore',
    'backbone',
], function($, _, Backbone){
    // App initialization logic here
});
