# usr/bin/env python
# -*-coding:utf-8 -*-

from django.conf.urls import url,include
from django.contrib import admin
from blog import views

urlpatterns = [

   url(r'^index/$',views.index,name='index'),
   url(r'^archive/$',views.archive,name='archive'),
   url(r'^article/$',views.article,name='article'),
   url(r'^login/$',views.do_login,name='login'),
   url(r'^reg/$',views.do_reg,name='reg'),
   url(r'^do_logout/$',views.do_logout,name='do_logout'),
   url(r'^comment/post/$', views.comment_post, name='comment_post'),
   url(r'^category/$',views.category,name='category'),
   url(r'^tag/$',views.tag,name='tag'),
]