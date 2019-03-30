# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User 
from django.db.models.signals import post_save
from django.dispatch import receiver

class Board(models.Model):
	name = models.CharField(max_length=30, unique=True)
	description = models.CharField(max_length=100)
	
	def __str__(self):
		return self.name 
		
	def get_posts_count(self):
		return Post.objects.filter(topic__board=self).count()
		
	def get_topic_count(self):
		return self.topics.count()
		
	def get_last_post(self):
		return Post.objects.filter(topic__board=self).order_by('-created_at').first()
	
class Topic(models.Model):
	subject = models.CharField(max_length=255)
	last_updated = models.DateTimeField(auto_now_add=True)
	board = models.ForeignKey(Board, related_name='topics')
	starter = models.ForeignKey(User, related_name='topics')
	views = models.PositiveIntegerField(default=0)
	
	def __str__(self):
		return self.subject
	
class Post(models.Model):
	message = models.TextField(max_length=4000)
	topic = models.ForeignKey(Topic, related_name='posts')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(null=True)
	created_by = models.ForeignKey(User, related_name='posts')
	updated_by = models.ForeignKey(User, null=True, related_name='+')
	
	def __str__(self):
		return self.message
		
		
	
class Estimate(models.Model):
	client = models.CharField(max_length=255)
	year = models.CharField(max_length=255)
	make = models.CharField(max_length=255)
	model = models.CharField(max_length=255)
	
	
	def __str__(self):
		return self.year + ' ' + self.make + ' ' + self.model 
		
		
class smPost(models.Model):
	text = models.CharField(max_length=255)
	last_updated = models.DateTimeField(auto_now_add=True)
	starter = models.ForeignKey(User, related_name='smpost')
	
	def __str__(self):
		return self.text 
	
	
class Comment(models.Model):
	commenttext = models.CharField(max_length=255)
	smpost = models.ForeignKey(smPost, related_name='comments')
	created_by = models.ForeignKey(User, related_name='comments') 
	
	def __str__(self):
		return self.commenttext 
	
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    steamid = models.TextField(max_length=500, blank=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()	


# Create your models here.
