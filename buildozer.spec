[app]
title = Python Music Player package.name = pythonmusicplayer package.domain = org.joaohenrique
source.dir = . source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,wav,ogg,flac,m4a,aac
version = 1.0
requirements = python3,kivy
orientation = portrait fullscreen = 0
android.api = 34 android.minapi = 23 android.ndk = 25b android.archs = arm64-v8a
android.permissions = android.permission.READ_MEDIA_AUDIO,android.permission.READ_EXTERNAL_STORAGE android.accept_sdk_license = True
android.debug_artifact = apk
log_level = 2 warn_on_root = 1
[buildozer]
log_level = 2 warn_on_root = 1
