/* jshint node: true */

'use strict';

var path = require('path');
var gulp = require('gulp');
var less = require('gulp-less');
var shell = require('gulp-shell');
var connect = require('gulp-connect');

gulp.task('server', function() {
    connect.server({
        root: 'src',
        port: 8801,
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
    var lessFiles = 'src/**/*.less';
    gulp.watch(lessFiles).on('change', function(event) {
        gulp.src(event.path)
            .pipe(less())
            .pipe(gulp.dest(path.dirname(event.path)));
    });

    var livereloadFiles = [
        'src/**/*.js',
        'src/**/*.css',
        'src/**/*.html',
    ];
    gulp.watch(livereloadFiles).on('change', function(event) {
        gulp.src(event.path).pipe(connect.reload());
    });
});

gulp.task('make-bower', shell.task('bower prune && bower install'));

gulp.task('make-less', function() {
    gulp.src('src/**/*.less')
        .pipe(less())
        .pipe(gulp.dest('./src/'));
});

gulp.task('make', ['make-bower', 'make-less']);

gulp.task('build', ['make'], function() {
    console.log('TODO');
});

gulp.task('default', ['make'], function() {
    gulp.run('server', 'watch');
});
