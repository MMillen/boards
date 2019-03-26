# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Board 
from .models import Estimate

admin.site.register(Board)
admin.site.register(Estimate)

# Register your models here.
