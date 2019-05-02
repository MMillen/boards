from django import forms 
from .models import Topic, Post, smPost, Comment, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class NewTopicForm(forms.ModelForm):
	message = forms.CharField(
		widget=forms.Textarea(attrs={'rows':5, 'placeholder': 'Whats on your mind?'}),
		max_length=4000,
		help_text = 'The max length of this field is 4000.'
		)
	
	class Meta:
		model = Topic 
		fields = ['subject', 'message']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message', ]
		
class SmPostForm(forms.ModelForm):

	text = forms.CharField(
		widget=forms.Textarea(attrs={'rows':5, 'placeholder': 'Whats on your mind?'}),
		max_length=4000
		)

	class Meta:
		model = smPost
		fields = ['text', ]
		
class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment 
		fields = ['commenttext' ]
		
		
class UserForm(forms.ModelForm):
	class Meta:
		model = User 
		fields = ('first_name', 'last_name', 'email')
		
class ProfileForm(forms.ModelForm):
	
	steamid = forms.CharField(
		widget = forms.Textarea(attrs={'rows':1}), max_length=20
		)
	class Meta:
		model = Profile 
		fields = ('steamid',)
		
		