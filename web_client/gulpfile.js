/* jshint node: true */

'use strict';

var gulp = require('gulp');
var connect = require('gulp-connect');

gulp.task('server', function() {
    connect.server({
        root: 'src',
        port: 8000,
        livereload: true,
        middleware: function(connect) {
            return [
                connect().use('/bower_components',
                connect.static('./bower_components')),
            ];
        },
    });
});

gulp.task('watch', function () {
    var livereloadFiles = [
        'src/**/*.js',
        'src/**/*.css',
        'src/**/*.html',
    ];
    gulp.watch(livereloadFiles).on('change', function(event) {
        gulp.src(event.path).pipe(connect.reload());
    });
});

gulp.task('default', function() {
    gulp.run('server', 'watch');
});
