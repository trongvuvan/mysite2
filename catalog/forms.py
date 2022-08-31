import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.forms import ModelForm

from .models import Book, Author, BookInstance, Genre
class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text=gettext('Enter a date between now and 4 weeks (default 3).'))

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        return data

class BookRequest(ModelForm):
    class Meta:
        model = BookInstance
        fields=['borrow']
        labels = {'borrow': gettext('borrow status')}

class CreateBookForm(forms.Form): 
    class Meta:
        model = Book
        fields='__all__'
        
    def __init__(self, *args, **kwargs):
        super(CreateBookForm, self).__init__(*args, **kwargs)
class CreateAuthorForm(forms.Form): 
    class Meta:
        model = Author
        fields='__all__'
        
    def __init__(self, *args, **kwargs):
        super(CreateAuthorForm, self).__init__(*args, **kwargs)

class BorrowBookForm(ModelForm):
    def clean_due_back(self):
        data = self.cleaned_data['due_back']

        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - borrow in past'))
        return data
    class Meta:
        model = BookInstance
        fields = ['due_back']
        labels = {'due_back': gettext('Return date')}