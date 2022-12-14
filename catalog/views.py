import datetime

from django.views import generic
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required,login_required, permission_required
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.contrib.messages import constants as messages

from catalog.models import Author
from catalog.forms import BorrowBookForm, RenewBookForm, CreateBookForm
from .models import Book, Author, BookInstance, Genre

def index(request):
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    num_authors = Author.objects.count()
    num_genre = Genre.objects.count()
    
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genre':num_genre,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 5
 
class BookDetailView(generic.DetailView):
    model = Book
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['copy_list'] = BookInstance.objects.all().filter(book=self.object)
        return context

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 5

class AuthorDetailView(generic.DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author_book_list'] = Book.objects.all().filter(author=self.object)
        return context

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 5

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user, status__exact='o').order_by('due_back')
class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 5

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')
@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre','release_day','cover']
    permission_required = 'catalog.can_mark_returned'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre','release_day','cover']
    permission_required = 'catalog.can_mark_returned'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
class BookSearch(generic.ListView):
    model = Book
    template_name = 'search/book_search.html'
    def get_queryset(self):  
        query = self.request.GET.get("book")   
        object_list = Book.objects.filter( 
            Q(title__icontains=query) | Q(genre__name=query) | Q(author__first_name=query) | Q(author__last_name=query)
        )
        return object_list 
class AuthorSearch(generic.ListView):
    model = Author
    template_name = 'search/author_search.html'
    def get_queryset(self):  
        query = self.request.GET.get("author")
        
        if str.isdigit(query) == 1:
            object_list = Author.objects.filter( 
                Q(first_name=query) | Q(last_name=query) | Q(date_of_birth__year = query)
            )
            return object_list
        else: 
            object_list = Author.objects.filter( 
                Q(first_name=query) | Q(last_name=query)
            )
            return object_list
# using modelform
@login_required
def BookBorrow(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = BorrowBookForm(request.POST)

        if form.is_valid():

            book_instance.borrow_day = datetime.date.today()
            book_instance.due_back = form.cleaned_data['due_back']
            book_instance.borrower = request.user
            book_instance.status = 'o'

            book_instance.save()

            return HttpResponseRedirect(reverse('my-borrowed'))

    else:
        proposed_rent_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = BorrowBookForm(initial={'due_back': proposed_rent_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_borrow.html', context)

# using modelform
@login_required
def BookReturn(request, pk):

    book_instance = get_object_or_404(BookInstance, pk=pk)

    book_instance.due_back = None
    book_instance.borrower = None
    book_instance.status = 'a'

    book_instance.save()
    return HttpResponseRedirect(reverse('my-borrowed'))
