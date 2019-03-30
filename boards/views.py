# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404, redirect 

from django.http import HttpResponse 

from django.contrib.auth.models import User 

from django.contrib.auth.decorators import login_required

from django.db.models import Count 

from django.views.generic import ListView

from django.urls import reverse_lazy

from django.utils.decorators import method_decorator 

from django.views.generic import UpdateView



from .models import Board, Topic, Post, smPost, Comment, Profile
from .models import Estimate

from .forms import NewTopicForm, PostForm, SmPostForm, CommentForm



import httplib, urllib, base64
import json 
import requests 


@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
	model = User 
	fields = ('first_name', 'last_name', 'email' )
	template_name = 'my_account.html'
	success_url = reverse_lazy('my_account')
	
	def get_object(self):
		return self.request.user 

def home(request):
	boards = Board.objects.all()
	return render(request, 'home.html', {'boards':boards})
	
class BoardListView(ListView):
	model = Board 
	context_object_name = 'boards'
	template_name = 'home.html'
	
def board_topics(request, pk):
	board = Board.objects.get(pk=pk)
	topics = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
	return render(request, 'topics.html', {'board':board, 'topics':topics})
	
def estimate(request, pk):
	estimate = Estimate.objects.get(pk=pk)
	return render(request, 'estimate.html', {'estimate':estimate})
	
@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    user = User.objects.first()
	
    if request.method == 'POST':
		form = NewTopicForm(request.POST)
		if form.is_valid():
			topic = form.save(commit=False)
			topic.board = board 
			topic.starter = request.user
			topic.save()
			post = Post.objects.create(
				message = form.cleaned_data.get('message'),
				topic=topic,
				created_by=request.user
			)
			return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
    else:
		form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form':form})
	
def topic_posts(request, pk, topic_pk):
	topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
	topic.views += 1
	topic.save() 
	return render(request, 'topic_posts.html', {'topic': topic})
	
	
@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
    else:
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


def api(request):
	uid = 1111
	req = requests.get("https://newsapi.org/v2/top-headlines?sources=cnbc&apiKey=79197463666045099e76d01879cd5be5")
	json_data = json.loads(req.content)

	Title = json_data['articles'][0]['title'].encode("utf-8").replace("'","") 

	return render(request, 'api.html',{'title':Title}) 
	
def smposts(request):
	Posts = smPost.objects.all().order_by('-last_updated')
	if request.method == 'POST':
		form = SmPostForm(request.POST)
		if form.is_valid():
			smpost = form.save(commit=False)
			smpost.starter = request.user 
			smpost.save()
			return redirect('smposts')
		else:
			return redirect('smposts')
			
		commentform = CommentForm(request.POST)
		if commentform.is_valid():
			comment = commentform.save(commit=False)
			comment.created_by = request.user 
			#comment.smpost= request.post.id 
			comment.save()
			return redirect('smposts')
	else:
		form = SmPostForm()
		commentForm = CommentForm()
	return render(request, 'smposts.html', {'posts':Posts, 'form':form, 'commentform':commentForm}) 
	
	
def commenttest(request):
	if request.method == 'POST':
		commentform = CommentForm(request.POST)
		if commentform.is_valid():
			comment = commentform.save(commit=False)
			comment.created_by = request.user 
			comment.save()
			return redirect('commenttest')
	else:
		commentForm = CommentForm()
	return render(request, 'commenttest.html', {'commentform':commentForm}) 		
	
	
def cbvposts(request):
	Posts = smPost.objects.all().order_by('-last_updated')
	if request.method == 'POST':
		form = SmPostForm(request.POST)
		commentform = CommentForm(request.POST, initial={'smpost': 'post.id'})
		success = False 
		if ('Post' in request.POST and form.is_valid()):
			smpost = form.save(commit=False)
			smpost.starter = request.user 
			smpost.save()	
			success = True
			
		if ('Comment' in request.POST and commentform.is_valid()):
			data = request.POST.copy()
			comment = commentform.save(commit=False)
			comment.created_by = request.user 
			comment.smpost_id= data.get('postid')
			comment.save()
			success = True
			
		if success:
			return redirect('cbvposts')
	else:
		form = SmPostForm()
		commentForm = CommentForm()
	return render(request, 'smposts.html', {'posts':Posts, 'form':form, 'commentform':commentForm}) 

# Create your views here.
