# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Board 
from .models import Estimate, smPost, Comment 

admin.site.register(Board)
admin.site.register(Estimate)
admin.site.register(smPost)
admin.site.register(Comment)

# Register your models here.
