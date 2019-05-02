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

from django.db import transaction



from .models import Board, Topic, Post, smPost, Comment, Profile
from .models import Estimate

from .forms import NewTopicForm, PostForm, SmPostForm, CommentForm, UserForm, ProfileForm



import httplib, urllib, base64
import json 
import requests 
import operator 
import collections
import numbers
import pandas as pd 
import numpy as np 
from scipy import stats as scistats

from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt












#------------------------------------------------------- CSGO Stats class 
class statsCSGO:
	def __init__(self, steamid):
		profile = requests.get("http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=E1A7AFDCEB3C011FAD2DA2BC3A581987&steamids=" + steamid +'"')
		profilejson = json.loads(profile.content)
		req = requests.get("https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=730&key=E1A7AFDCEB3C011FAD2DA2BC3A581987&steamid=" + steamid + '"')
		json_data = json.loads(req.content)

		stats = json_data['playerstats']['stats']
		KillsDict = {}
		ShotsDict = {}
		HitsDict = {}
		ShotsFired = 0
		ShotsHit = 0
		
		
		for each in stats:
			if each['name'] == 'total_kills':
				kills = float(each['value'])
			if each['name'] == 'total_deaths':
				deaths = float(each['value'])
			if each['name'] == 'total_matches_played':
				matches = float(each['value'])
			if each['name'] == 'total_contribution_score':
				score = float(each['value'])
				
			if 'total_kills_' in each['name']:
				weapon = each['name'].split('kills_')[1]
				if '_' not in weapon and 'headshot' not in weapon:
					KillsDict[weapon] = each['value']

			if 'total_shots_' in each['name']:
				weapon = each['name'].split('shots_')[1]
				if '_' not in weapon and 'fired' not in weapon:
					ShotsDict[weapon] = each['value']	



			if 'total_hits_' in each['name']:
				weapon = each['name'].split('hits_')[1]
				if '_' not in weapon and 'fired' not in weapon:
					HitsDict[weapon] = each['value']




			if each['name'] == 'total_shots_fired':
				ShotsFired = float(each['value'])
			if each['name'] == 'total_shots_hit':
				ShotsHit = float(each['value'])
		
		sortedKills = sorted(KillsDict.items(), key=operator.itemgetter(1), reverse=True)
		top3Weapon = sortedKills[0:3]
		self.TopWeapon = top3Weapon[0][0].upper()
		self.TopWeaponKills = top3Weapon[0][1]
		self.SecondWeapon = top3Weapon[1][0].upper()
		self.SecondWeaponKills = top3Weapon[1][1]
		self.ThirdWeapon = top3Weapon[2][0].upper()
		self.ThirdWeaponKills = top3Weapon[2][1]
		
		self.KillsDict = KillsDict
		self.ShotsDict = ShotsDict 
		self.HitsDict = HitsDict 
		
		self.kills = kills 
		self.deaths = deaths 
		self.matches = matches 
		self.score = score 
		
		self.killspermatch = int(kills/matches) 
		self.scorepermatch = int(score/matches)
		
		self.accuracy = int(round(float(ShotsHit/ShotsFired), 2) * 100)
		#print profilejson#['response']['players']['steamid']

		self.KDR = str(round((kills/deaths),1)) + ":1"
		
		
		
		profile = profilejson['response']['players'][0]

		self.name = profile['personaname']
		self.avatar = profile['avatarfull']
		
		
#-----------------------------------------------------------------------------------------------------------------------------
	#Steam Profile Class

class steamProfile:
	def __init__(self, steamid):
		profile = requests.get("http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=E1A7AFDCEB3C011FAD2DA2BC3A581987&steamids=" + steamid +'"')
		profilejson = json.loads(profile.content)
		
		profile = profilejson['response']['players'][0]

		self.name = profile['personaname']
		self.avatar = profile['avatarfull']
			
#-----------------------------------------------------		
		


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
	
	
@login_required
@transaction.atomic 
def update_profile(request):
	if request.user.is_authenticated():
		steam = request.user.profile.steamid
	else:
		return redirect(login)
	try:
		stats = steamProfile(str(steam))
	except:
		stats = 'null'
	if request.method == 'POST':
		user_form = UserForm(request.POST, instance=request.user)
		profile_form = ProfileForm(request.POST, instance=request.user.profile)
		if user_form.is_valid() and profile_form.is_valid():
			user_form.save()
			profile_form.save()
			return render(request, 'loading.html')
		else:
			return render(request, 'profile.html', {'user_form':user_form,'profile_form':profile_form, 'stats':stats})
	else:
		user_form = UserForm(instance=request.user)
		profile_form = ProfileForm(instance=request.user.profile)		
	return render(request, 'profile.html', {'user_form':user_form,'profile_form':profile_form, 'stats':stats})
	
def update_loading(request):
	return render(request, 'loading.html')
	
	
@login_required	
def csgostats(request):
	steam = request.user.profile.steamid
	
	try:
		profile = steamProfile(str(steam))
		ProfileValid = True 
	except:
		ProfileValid = False 

	if ProfileValid != True:
		return render(request, 'invalidsteamid.html')

	#--------------------------------------------------------------------------------------generate stats object, assign basic vriables 
	stats = statsCSGO(str(steam))
	KillDict = dict(stats.KillsDict)
	KillDict = sorted(KillDict.items(), key=operator.itemgetter(1), reverse=True)
	KillDict = collections.OrderedDict(KillDict)
	Shots = sum(stats.ShotsDict.values())
	Hits = sum(stats.HitsDict.values())
	killspermatch = stats.killspermatch 
	scorepermatch = stats.scorepermatch
	#-------------------------------------------------------------------------------------generate numbers for server side html table rendering 
	try:
		overallHitsToKill = str(round((float(Hits)/float(stats.kills)),1)) + ":1"
	except:
		overallHitsToKill = "0"
		
	try:
		overallAccuracy = (float(Hits)/float(Shots))
		overallAccuracy = int(round(overallAccuracy, 2) * 100)
	except:
		overallAccuracy = "0"
		
	
	try:
		top3Kills = dict(collections.Counter(stats.KillsDict).most_common()[:3])
		top3Kills = sum(top3Kills.values())
	except:
		top3Kills = 0
	try:
		top3Hits = dict(collections.Counter(stats.HitsDict).most_common()[:3])
		top3Hits = sum(top3Hits.values())
	except:
		top3Hits = 0
	try:
		top3Shots = dict(collections.Counter(stats.ShotsDict).most_common()[:3])
		top3Shots = sum(top3Shots.values())
	except:
		top3Shots = 0
	try:
		top3HitsToKill = str(round((float(top3Hits)/float(top3Kills)),1)) + ":1"
	except:
		top3HitsToKill = "0"
	try:
		top3Accuracy = (float(top3Hits)/float(top3Shots))
		top3Accuracy = int(round(top3Accuracy, 2) * 100)
	except:
		top3Accuracy = "0"
		
	

	#---------------------------------------------------------------------------------------------------generate variables for team bias and weapon recommendations
		#--------------------------------------------------------- Compare shots fired with T asd CT weapons, assumption is more shots fired with t specific weapons than ct mean player is biased t, and vice versa 
	shotsFiredCT = 0
	try:
		for key, value in stats.ShotsDict.iteritems():
			if str(key) == 'm4a1' or str(key) == 'aug' or str(key) == 'famas':
				shotsFiredCT += int(value)
	except:
		shotsFiredCT = 0
		
	shotsFiredT = 0
	try:
		for key, value in stats.ShotsDict.iteritems():
			if str(key) == 'ak47' or str(key) == 'sg556' or str(key) == 'galilar' or str(key) == 'mac10' or str(key) == 'g3sg1':
				shotsFiredT += int(value)
				
	except:
		shotsFiredT = 0
		

	#---------------------------------------------------------------calculate team bias based on shots fired with team specific weapons	
	TeamBias = 'NULL'
	if shotsFiredCT > shotsFiredT:
		TeamBias = 'Counter-Terrorist'
	else:
		TeamBias = "Terrorist"
		
	#------------------------------------------------------------calculate team bias percentage by comparing shots fired by team specific weapons 	
	PercentTeamBias = 0
	if TeamBias == 'NULL':
		PercentTeamBias = 0
	if TeamBias == 'Counter-Terrorist':
		PercentTeamBias = (float(shotsFiredCT)/float(shotsFiredCT + shotsFiredT))
		PercentTeamBias = int(round(PercentTeamBias, 2) * 100)
	else:
		PercentTeamBias = (float(shotsFiredT)/float(shotsFiredCT + shotsFiredT))
		PercentTeamBias = int(round(PercentTeamBias, 2) * 100)		
		
	Team = str(TeamBias)
	PercentTeamBiasString = str(PercentTeamBias) + "%"
		
		
	#-------------------------------------------------------declare variables for feedback function 	
	M4A1_Accuracy = 0 
	AUG_Accuracy = 0 
	AK47_Accuracy = 0
	SG556_Accuracy = 0 
	M4A1_HTK = 0 
	AUG_HTK = 0 
	AK47_HTK = 0
	SG556_HTK = 0 
	M4A1_Shots = int(stats.ShotsDict['m4a1']) 
	AUG_Shots = int(stats.ShotsDict['aug']) 
	AK47_Shots = int(stats.ShotsDict['ak47'])
	SG556_Shots = int(stats.ShotsDict['sg556'])
	
	def generateTeamFeedback():
		if Team == 'Counter-Terrorist':
			if M4A1_Shots > AUG_Shots:
				if M4A1_Accuracy > AK47_Accuracy and M4A1_HTK >= AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					return output
				if M4A1_Accuracy > AK47_Accuracy and M4A1_HTK < AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					output = output + ' and are' + str(round(((float(M4A1_HTK)-float(AK47_HTK))/float(AK47_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if M4A1_Accuracy < AK47_Accuracy and M4A1_HTK <= AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, however you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the M4A1'
					return output
				if M4A1_Accuracy < AK47_Accuracy and M4A1_HTK > AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, however you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					output = output + ' and your hit to kill ratio with the AK47 is superior by ' + str(M4A1_HTK - AK47_HTK) +'. You should consider shifting your bias to T.'

					return output						

			if M4A1_Shots < AUG_Shots:
				if AUG_Accuracy > SG556_Accuracy and AUG_HTK >= SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					return output
				if AUG_Accuracy > SG556_Accuracy and AUG_HTK < SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					output = output + ' and are' + str(round(((float(AUG_HTK)-float(SG556_HTK))/float(SG556_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if AUG_Accuracy < SG556_Accuracy and AUG_HTK <= SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, however you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the AUG'
					return output
				if AUG_Accuracy < SG556_Accuracy and AUG_HTK > SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, however you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					output = output + ' and your hit to kill ratio with the SG556 is superior by ' + str(AUG_HTK - SG556_HTK) +'. You should consider shifting your bias to T.'

					return output	

					
		else:

			if AK47_Shots > SG556_Shots:
				if AK47_Accuracy > M4A1_Accuracy and AK47_HTK >= M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					return output
				if AK47_Accuracy > M4A1_Accuracy and AK47_HTK < M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					output = output + ' and are' + str(round(((float(AK47_HTK)-float(M4A1_HTK))/float(M4A1_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if AK47_Accuracy < M4A1_Accuracy and AK47_HTK <= M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, however you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the AK47'
					return output
				if AK47_Accuracy < M4A1_Accuracy and AK47_HTK > M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, however you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					output = output + ' and your hit to kill ratio with the M4A1 is superior by ' + str(AK47_HTK - M4A1_HTK) +'. You should consider shifting your bias to T.'

					return output						

			if AK47_Shots < SG556_Shots:
				if SG556_Accuracy > AUG_Accuracy and SG556_HTK >= AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					return output
				if SG556_Accuracy > AUG_Accuracy and SG556_HTK < AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					output = output + ' and are' + str(round(((float(SG556_HTK)-float(AUG_HTK))/float(AUG_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if SG556_Accuracy < AUG_Accuracy and SG556_HTK <= AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, however you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the SG556'
					return output
				if SG556_Accuracy < AUG_Accuracy and SG556_HTK > AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, however you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					output = output + ' and your hit to kill ratio with the AUG is superior by ' + str(SG556_HTK - AUG_HTK) +'. You should consider shifting your bias to T.'

					return output						
			return ""		
			
	
	
	html = "<table class='w3-table w3-striped w3-bordered w3-border w3-grey w3-tiny w3-hoverable w3-card w3-black'><tr class='w3-deep-purple'><th>Weapon</th><th>Kills</th><th>Hits</th><th>Hit to Kill Ratio</th><th>Shots Fired</th><th>Accuracy</th></tr>"
	html = html + "<tr style='font-size:18px;'><td>Overall</td><td>"+str(int(stats.kills))+"</td><td>"+str(Hits)+"</td><td>"+overallHitsToKill+"</td><td>"+str(Shots)+"</td><td>"+str(overallAccuracy)+"%</td></tr>"
	html = html + "<tr style='font-size:14px;'><td>Top 3:</td><td>"+str(top3Kills)+"</td><td>"+str(top3Hits)+"</td><td>"+top3HitsToKill+"</td><td>"+str(top3Shots)+"</td><td>"+str(top3Accuracy)+"%</td></tr>"
	for key, value in KillDict.iteritems():
		weapon = str(key)
		try:
			kills = int(value)
		except:
			kills = 0 
		try:
			shots = int(stats.ShotsDict[weapon])
		except:
			shots = 0 
		try:
			hits = int(stats.HitsDict[weapon])
		except:
			hits = 0
		try:
			Accuracy = (float(hits)/float(shots))
			Accuracy = int(round(Accuracy, 2) * 100)
			if str(key) == 'm4a1':
				M4A1_Accuracy = Accuracy

			if str(key) == 'aug':
				AUG_Accuracy = Accuracy

			if str(key) == 'ak47':
				AK47_Accuracy = Accuracy

			if str(key) == 'sg556':
				SG556_Accuracy = Accuracy

		except:
			Accuracy = 0
		try:
			HitsToKill = round((hits/kills),1)
			if str(key) == 'm4a1':
				M4A1_HTK = HitsToKill

			if str(key) == 'aug':
				AUG_HTK = HitsToKill

			if str(key) == 'ak47':
				AK47_HTK = HitsToKill

			if str(key) == 'sg556':
				SG556_HTK = HitsToKill			
		except:
			HitsToKill = 'N/A'
		html = html + "<tr><td><b>"+ str(key).upper() + "</b></td>"
		html = html + "<td>"+ str(kills) + "</td>"
		html = html + "<td>"+ str(hits) + "</td>"
		html = html + "<td>"+ str(HitsToKill) + ":1</td>"
		html = html + "<td>"+ str(shots) + "</td>"
		html = html + "<td>"+str(Accuracy)+"%</td></tr>"
		
	html = html + "</table>"
	
	acc = overallAccuracy

	overalldata = pd.read_csv('static\ids2.csv')

	kdrs = []
	accurs = []


	kdr = str(stats.KDR).split(':')[0] 
	

	kdrpatch = int(float(kdr) * 5)
	for i in range(len(overalldata.kdr)):
		kdrs.append(overalldata.kdr[i])
		accurs.append(overalldata.accuracy[i])
		
	kdrtitle = "Your KDR of " + str(kdr) + " is in the top " + str(int(scistats.percentileofscore(kdrs,float(kdr), kind='strict') )) +"th percentile of all player data on record."
	n, bins, patches = plt.hist(kdrs, bins=np.arange(0, 4, 0.2), align='left', color='g',facecolor='lightslategray')
	patches[kdrpatch].set_fc('r')
	plt.title(kdrtitle)
	buf = BytesIO()
	plt.savefig(buf, format='png')
	kdrimage = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()
	plt.close()
	plt.clf()
	
	
	

	accpatch = int(acc)-5
		
	acctitle = "Your Accuracy of " + str(acc) + "% is in the top " + str(int(np.percentile(accurs, acc) )) +"th percentile of all player data on record."

	n, bins, patches = plt.hist(accurs, bins=np.arange(5, 25, 1), align='left', color='g',facecolor='lightslategray')
	patches[accpatch].set_fc('r')

	plt.title(acctitle)
	buf = BytesIO()
	plt.savefig(buf, format='png')
	accimage = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()
	plt.close()
		
	
	try:
		return render(request, 'csgostats.html', context = {'steam':steam,'stats':stats,  'html':html, 'acc':acc,
			'killspermatch': killspermatch, 'scorepermatch':scorepermatch, 'team':Team,'percentteambias':PercentTeamBiasString, 'testvar':generateTeamFeedback(), 'kdrimage':kdrimage, 'accimage':accimage} )
		

	except:
		if ProfileValid != True:
			return render(request, 'invalidsteamid.html')
		if ProfileValid == True:
			return render(request, 'invalidsteamid.html')
		if request.user.is_authenticated() == False:
			return redirect(login)
		#return render(request, 'invalidsteamid.html')
		
		


# Create your views here.








def liveplot(request):
	plt.plot(range(10))
	buf = BytesIO()
	plt.savefig(buf, format='png')
	image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()
	return render(request, 'liveplot.html',{'image_base64':image_base64}) 



















































@login_required	
def csgostatstest(request):
	steam = request.user.profile.steamid
	
	try:
		profile = steamProfile(str(steam))
		ProfileValid = True 
	except:
		ProfileValid = False 

	if ProfileValid != True:
		return render(request, 'invalidsteamid.html')

	#--------------------------------------------------------------------------------------generate stats object, assign basic vriables 
	stats = statsCSGO(str(steam))
	KillDict = dict(stats.KillsDict)
	KillDict = sorted(KillDict.items(), key=operator.itemgetter(1), reverse=True)
	KillDict = collections.OrderedDict(KillDict)
	Shots = sum(stats.ShotsDict.values())
	Hits = sum(stats.HitsDict.values())
	killspermatch = stats.killspermatch 
	scorepermatch = stats.scorepermatch
	#-------------------------------------------------------------------------------------generate numbers for server side html table rendering 
	try:
		overallHitsToKill = str(round((float(Hits)/float(stats.kills)),1)) + ":1"
	except:
		overallHitsToKill = "0"
		
	try:
		overallAccuracy = (float(Hits)/float(Shots))
		overallAccuracy = int(round(overallAccuracy, 2) * 100)
	except:
		overallAccuracy = "0"
		
	
	try:
		top3Kills = dict(collections.Counter(stats.KillsDict).most_common()[:3])
		top3Kills = sum(top3Kills.values())
	except:
		top3Kills = 0
	try:
		top3Hits = dict(collections.Counter(stats.HitsDict).most_common()[:3])
		top3Hits = sum(top3Hits.values())
	except:
		top3Hits = 0
	try:
		top3Shots = dict(collections.Counter(stats.ShotsDict).most_common()[:3])
		top3Shots = sum(top3Shots.values())
	except:
		top3Shots = 0
	try:
		top3HitsToKill = str(round((float(top3Hits)/float(top3Kills)),1)) + ":1"
	except:
		top3HitsToKill = "0"
	try:
		top3Accuracy = (float(top3Hits)/float(top3Shots))
		top3Accuracy = int(round(top3Accuracy, 2) * 100)
	except:
		top3Accuracy = "0"
		
	

	#---------------------------------------------------------------------------------------------------generate variables for team bias and weapon recommendations
		#--------------------------------------------------------- Compare shots fired with T asd CT weapons, assumption is more shots fired with t specific weapons than ct mean player is biased t, and vice versa 
	shotsFiredCT = 0
	try:
		for key, value in stats.ShotsDict.iteritems():
			if str(key) == 'm4a1' or str(key) == 'aug' or str(key) == 'famas':
				shotsFiredCT += int(value)
	except:
		shotsFiredCT = 0
		
	shotsFiredT = 0
	try:
		for key, value in stats.ShotsDict.iteritems():
			if str(key) == 'ak47' or str(key) == 'sg556' or str(key) == 'galilar' or str(key) == 'mac10' or str(key) == 'g3sg1':
				shotsFiredT += int(value)
				
	except:
		shotsFiredT = 0
		

	#---------------------------------------------------------------calculate team bias based on shots fired with team specific weapons	
	TeamBias = 'NULL'
	if shotsFiredCT > shotsFiredT:
		TeamBias = 'Counter-Terrorist'
	else:
		TeamBias = "Terrorist"
		
	#------------------------------------------------------------calculate team bias percentage by comparing shots fired by team specific weapons 	
	PercentTeamBias = 0
	if TeamBias == 'NULL':
		PercentTeamBias = 0
	if TeamBias == 'Counter-Terrorist':
		PercentTeamBias = (float(shotsFiredCT)/float(shotsFiredCT + shotsFiredT))
		PercentTeamBias = int(round(PercentTeamBias, 2) * 100)
	else:
		PercentTeamBias = (float(shotsFiredT)/float(shotsFiredCT + shotsFiredT))
		PercentTeamBias = int(round(PercentTeamBias, 2) * 100)		
		
	Team = str(TeamBias)
	PercentTeamBiasString = str(PercentTeamBias) + "%"
		
		
	#-------------------------------------------------------declare variables for feedback function 	
	M4A1_Accuracy = 0 
	AUG_Accuracy = 0 
	AK47_Accuracy = 0
	SG556_Accuracy = 0 
	M4A1_HTK = 0 
	AUG_HTK = 0 
	AK47_HTK = 0
	SG556_HTK = 0 
	M4A1_Shots = int(stats.ShotsDict['m4a1']) 
	AUG_Shots = int(stats.ShotsDict['aug']) 
	AK47_Shots = int(stats.ShotsDict['ak47'])
	SG556_Shots = int(stats.ShotsDict['sg556'])
	
	def generateTeamFeedback():
		if Team == 'Counter-Terrorist':
			if M4A1_Shots > AUG_Shots:
				if M4A1_Accuracy > AK47_Accuracy and M4A1_HTK >= AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					return output
				if M4A1_Accuracy > AK47_Accuracy and M4A1_HTK < AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					output = output + ' and are' + str(round(((float(M4A1_HTK)-float(AK47_HTK))/float(AK47_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if M4A1_Accuracy < AK47_Accuracy and M4A1_HTK <= AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, however you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the M4A1'
					return output
				if M4A1_Accuracy < AK47_Accuracy and M4A1_HTK > AK47_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the M4A1, however you are ' + str(abs(round(((float(M4A1_Accuracy)-float(AK47_Accuracy))/float(AK47_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					output = output + ' and your hit to kill ratio with the AK47 is superior by ' + str(M4A1_HTK - AK47_HTK) +'. You should consider shifting your bias to T.'

					return output						

			if M4A1_Shots < AUG_Shots:
				if AUG_Accuracy > SG556_Accuracy and AUG_HTK >= SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					return output
				if AUG_Accuracy > SG556_Accuracy and AUG_HTK < SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					output = output + ' and are' + str(round(((float(AUG_HTK)-float(SG556_HTK))/float(SG556_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if AUG_Accuracy < SG556_Accuracy and AUG_HTK <= SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, however you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the AUG'
					return output
				if AUG_Accuracy < SG556_Accuracy and AUG_HTK > SG556_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AUG, however you are ' + str(abs(round(((float(AUG_Accuracy)-float(SG556_Accuracy))/float(SG556_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					output = output + ' and your hit to kill ratio with the SG556 is superior by ' + str(AUG_HTK - SG556_HTK) +'. You should consider shifting your bias to T.'

					return output	

					
		else:

			if AK47_Shots > SG556_Shots:
				if AK47_Accuracy > M4A1_Accuracy and AK47_HTK >= M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					return output
				if AK47_Accuracy > M4A1_Accuracy and AK47_HTK < M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK47 than the M4A1'
					output = output + ' and are' + str(round(((float(AK47_HTK)-float(M4A1_HTK))/float(M4A1_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if AK47_Accuracy < M4A1_Accuracy and AK47_HTK <= M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, however you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the AK47'
					return output
				if AK47_Accuracy < M4A1_Accuracy and AK47_HTK > M4A1_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the AK47, however you are ' + str(abs(round(((float(AK47_Accuracy)-float(M4A1_Accuracy))/float(M4A1_Accuracy)), 2) *100)) + '% more accurate with the M4A1 than the AK47'
					output = output + ' and your hit to kill ratio with the M4A1 is superior by ' + str(AK47_HTK - M4A1_HTK) +'. You should consider shifting your bias to T.'

					return output						

			if AK47_Shots < SG556_Shots:
				if SG556_Accuracy > AUG_Accuracy and SG556_HTK >= AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					return output
				if SG556_Accuracy > AUG_Accuracy and SG556_HTK < AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the SG556 than the AUG'
					output = output + ' and are' + str(round(((float(SG556_HTK)-float(AUG_HTK))/float(AUG_HTK)), 2) *100) + '% better with hits to kills.'
					return output
				if SG556_Accuracy < AUG_Accuracy and SG556_HTK <= AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, however you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the AK57 than the SG556'
					return output
				if SG556_Accuracy < AUG_Accuracy and SG556_HTK > AUG_HTK:
					output = 'Your Counter-Terrorist weapon of choice is the SG556, however you are ' + str(abs(round(((float(SG556_Accuracy)-float(AUG_Accuracy))/float(AUG_Accuracy)), 2) *100)) + '% more accurate with the AUG than the SG556'
					output = output + ' and your hit to kill ratio with the AUG is superior by ' + str(SG556_HTK - AUG_HTK) +'. You should consider shifting your bias to T.'

					return output						
			return ""		
			
	
	
	html = "<table class='w3-table w3-striped w3-bordered w3-border w3-grey w3-tiny w3-hoverable w3-card w3-black'><tr class='w3-deep-purple'><th>Weapon</th><th>Kills</th><th>Hits</th><th>Hit to Kill Ratio</th><th>Shots Fired</th><th>Accuracy</th></tr>"
	html = html + "<tr style='font-size:18px;'><td>Overall</td><td>"+str(int(stats.kills))+"</td><td>"+str(Hits)+"</td><td>"+overallHitsToKill+"</td><td>"+str(Shots)+"</td><td>"+str(overallAccuracy)+"%</td></tr>"
	html = html + "<tr style='font-size:14px;'><td>Top 3:</td><td>"+str(top3Kills)+"</td><td>"+str(top3Hits)+"</td><td>"+top3HitsToKill+"</td><td>"+str(top3Shots)+"</td><td>"+str(top3Accuracy)+"%</td></tr>"
	for key, value in KillDict.iteritems():
		weapon = str(key)
		try:
			kills = int(value)
		except:
			kills = 0 
		try:
			shots = int(stats.ShotsDict[weapon])
		except:
			shots = 0 
		try:
			hits = int(stats.HitsDict[weapon])
		except:
			hits = 0
		try:
			Accuracy = (float(hits)/float(shots))
			Accuracy = int(round(Accuracy, 2) * 100)
			if str(key) == 'm4a1':
				M4A1_Accuracy = Accuracy

			if str(key) == 'aug':
				AUG_Accuracy = Accuracy

			if str(key) == 'ak47':
				AK47_Accuracy = Accuracy

			if str(key) == 'sg556':
				SG556_Accuracy = Accuracy

		except:
			Accuracy = 0
		try:
			HitsToKill = round((hits/kills),1)
			if str(key) == 'm4a1':
				M4A1_HTK = HitsToKill

			if str(key) == 'aug':
				AUG_HTK = HitsToKill

			if str(key) == 'ak47':
				AK47_HTK = HitsToKill

			if str(key) == 'sg556':
				SG556_HTK = HitsToKill			
		except:
			HitsToKill = 'N/A'
		html = html + "<tr><td><b>"+ str(key).upper() + "</b></td>"
		html = html + "<td>"+ str(kills) + "</td>"
		html = html + "<td>"+ str(hits) + "</td>"
		html = html + "<td>"+ str(HitsToKill) + ":1</td>"
		html = html + "<td>"+ str(shots) + "</td>"
		html = html + "<td>"+str(Accuracy)+"%</td></tr>"
		
	html = html + "</table>"
	
	acc = overallAccuracy
	
	
	
	
	
	
	overalldata = pd.read_csv('static\ids2.csv')

	kdrs = []
	accurs = []


	kdr = str(stats.KDR).split(':')[0] 
	

	kdrpatch = int(float(kdr) * 5)
	for i in range(len(overalldata.kdr)):
		kdrs.append(overalldata.kdr[i])
		accurs.append(overalldata.accuracy[i])
		
	kdrtitle = "Your KDR of " + str(kdr) + " is in the top " + str(int(scistats.percentileofscore(kdrs,float(kdr), kind='strict') )) +"th percentile of all player data on record."
	values =  np.random.randint(51, 140, 1000)
	n, bins, patches = plt.hist(kdrs, bins=np.arange(0, 4, 0.2), align='left', color='g',facecolor='lightslategray')
	patches[kdrpatch].set_fc('r')
	plt.title(kdrtitle)
	buf = BytesIO()
	plt.savefig(buf, format='png')
	kdrimage = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()
	plt.close()
	
	
	

	accpatch = int(acc)-5
		
	acctitle = "Your Accuracy of " + str(acc) + "% is in the top " + str(int(np.percentile(accurs, acc) )) +"th percentile of all player data on record."

	n, bins, patches = plt.hist(accurs, bins=np.arange(5, 25, 1), align='left', color='g',facecolor='lightslategray')
	patches[accpatch].set_fc('r')

	plt.title(acctitle)
	buf = BytesIO()
	plt.savefig(buf, format='png')
	accimage = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()
	
		
	
	try:
		return render(request, 'csgostatstest.html', context = {'steam':steam,'stats':stats,  'html':html, 'acc':acc,
			'killspermatch': killspermatch, 'scorepermatch':scorepermatch, 'team':Team,'percentteambias':PercentTeamBiasString, 'testvar':generateTeamFeedback(), 'kdrimage':kdrimage, 'accimage':accimage} )
		

	except:
		if ProfileValid != True:
			return render(request, 'invalidsteamid.html')
		if ProfileValid == True:
			return render(request, 'invalidsteamid.html')
		if request.user.is_authenticated() == False:
			return redirect(login)
		#return render(request, 'invalidsteamid.html')
		
		


# Create your views here.

