[app]
title = HP Sales App
package.name = HPDistributorsSR
package.domain = org.zjprograms

source.dir = .

source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,db,ttf,mbtiles

version = 0.1

requirements = python3,kivy==2.2.1,requests,plyer,pyjnius,mercantile

presplash.filename = logo.png
icon.filename = icon.png

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

android.api = 35
android.minapi = 21

android.ndk = 25b

android.accept_sdk_license = True

android.archs = arm64-v8a

android.copy_libs = 1

android.logcat_filters = *:S python:D

android.allow_backup = True

android.no-byte-compile-python = False

[buildozer]

log_level = 2
warn_on_root = 1