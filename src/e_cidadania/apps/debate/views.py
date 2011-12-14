# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Written by: Oscar Carballal Prego <info@oscarcp.com>
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

"""
These are the views that control the debates.
"""
# JSON stuff
import json

# Generic class-based views
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

# Decorators. the first is a wrapper to convert function-based decorators
# to method decorators that can be put in subclass methods.
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required

# Response types
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect

# Some extras
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext
from django.forms.formsets import formset_factory, BaseFormSet
from django.core.context_processors import csrf

# Function-based views
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, update_object
from django.views.generic.create_update import delete_object

# Application models
from e_cidadania.apps.debate.models import Debate, Note, Row, Column
from e_cidadania.apps.debate.forms import DebateForm, UpdateNoteForm, \
    NoteForm, RowForm, ColumnForm
from e_cidadania.apps.spaces.models import Space

def add_new_debate(request, space_name):

    """
    Create a new debate. This function returns two forms to create
    a complete debate, debate form and phases formset.
    """
    place = get_object_or_404(Space, url=space_name)
    
    # Define FormSets
    
    # This class is used to make empty formset forms required
    # See http://stackoverflow.com/questions/2406537/django-formsets-make-first-required/4951032#4951032
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    RowFormSet = formset_factory(RowForm, max_num=10, formset=RequiredFormSet)
    ColumnFormSet = formset_factory(ColumnForm, max_num=10, formset=RequiredFormSet)
   
    debate_form = DebateForm(request.POST or None)
    row_formset = RowFormSet(request.POST or None, prefix="rowform")
    column_formset = ColumnFormSet(request.POST or None, prefix="colform")

    # Get the last PK and add 1 to get the current PK
    try:
        last_debate_id = Debate.objects.latest('id')
        current_debate_id = last_debate_id.pk + 1
    except:
        current_debate_id = 1

    if request.user.has_perm('debate_add') or request.user.is_staff:
        if request.method == 'POST':
            if debate_form.is_valid() and row_formset.is_valid() and column_formset.is_valid():
                debate_form_uncommited = debate_form.save(commit=False)
                debate_form_uncommited.space = place
                debate_form_uncommited.author = request.user

                saved_debate = debate_form_uncommited.save()
                debate_instance = get_object_or_404(Debate, pk=current_debate_id)
 
                for form in row_formset.forms:
                    row = form.save(commit=False)
                    row.debate = debate_instance
                
                for form in column_formset.forms:
                    column = form.save(commit=False)
                    column.debate = debate_instance
                                
                return redirect('/spaces/' + space_name + '/debate/' + str(debate_form_uncommited.id))
                
        return render_to_response('debate/debate_add_simple.html',
                                  {'form': debate_form,
                                   'rowform': row_formset,
                                   'colform': column_formset,
                                   'get_place': place,
                                   'debateid': current_debate_id},
                                  context_instance=RequestContext(request))
            
    return render_to_response('not_allowed.html',
                              context_instance=RequestContext(request))
    
def get_debates(request):

    """
    Get all debates and serve them through JSON.
    """
    data = [debate.title for debate in Debate.objects.all().order_by('title')]
    return render_to_response(json.dumps(data), content_type='application/json')

def create_note(request, space_name):

    """
    Saves the note content and position within the table. This function is
    meant to be called as AJAX.
    """
    note_form = NoteForm(request.POST or None)
        
    if request.method == "POST" and request.is_ajax:        
        if note_form.is_valid():
            note_form_uncommited = note_form.save(commit=False)
            note_form_uncommited.author = request.user
            note_form_uncommited.debate = get_object_or_404(Debate,
                                                            pk=request.POST['debateid'])
            note_form_uncommited.title = request.POST['title']
            note_form_uncommited.message = request.POST['message']

            note_form_uncommited.save()
            msg = "The note has been created."

        else:
            msg = "The note form didn't validate. This fields gave errors: " \
            + str(note_form.errors)
    else:
        msg = "The petition was not POST."
        
    return HttpResponse(msg)
    
def update_note(request, space_name):

    """
    Create a new note with default data.
    """
    place = get_object_or_404(Space, url=space_name)
    note = get_object_or_404(Note, pk=request.POST['noteid'])
    # We are not using the request.POSt for the form since
    # it's incomplete and destroys information.
    note_form = UpdateNoteForm(request.POST or None, instance=note)
    msg = "Nothing to save."
        
    if request.method == "POST" and request.is_ajax:        
        if note_form.is_valid():
            note_form_uncommited = note_form.save(commit=False)
            note_form_uncommited.column = get_object_or_404(Column, pk=request.POST['column'])
            note_form_uncommited.row = get_object_or_404(Row, pk=request.POST['row'])
            note_form_uncommited.title = request.POST['title']
            note_form_uncommited.message = request.POST['message']
        
            note_form_uncommited.save()
            msg = "The note has been updated."
        else:
            msg = "The form is not valid, check field(s): " + note_form.errors
    else:
        msg = "There was some error in the petition."
        
    return HttpResponse(msg)


def delete_note(request, space_name):

    """
    Deletes a note object.
    """
    note = get_object_or_404(Note, noteid=request.POST['noteid'])
    
    if note.pub_author == request.user:
        note.delete()
        return HttpResponse("The note has been deleted.")
    
    else:
        return HttpResponse("You're not the author of the note. Can't delete")
        
class ViewDebate(DetailView):
    """
    View a debate.
    """
    context_object_name = 'debate'
    template_name = 'debate/debate_view.html'
    
    def get_object(self):
        debate = get_object_or_404(Debate, pk=self.kwargs['debate_id'])
        return debate    
    
    def get_context_data(self, **kwargs):
        """
        
        """
        context = super(ViewDebate, self).get_context_data(**kwargs)
        columns = Column.objects.all().filter(debate=self.kwargs['debate_id'])
        rows = Row.objects.all().filter(debate=self.kwargs['debate_id'])
        current_space = get_object_or_404(Space, url=self.kwargs['space_name'])
        current_debate = get_object_or_404(Debate, pk=self.kwargs['debate_id'])
        notes = Note.objects.all().filter(debate=current_debate.pk)
        try:
            last_note = Note.objects.latest('id')
        except:
            last_note = 0

        context['get_place'] = current_space  
        context['notes'] = notes
        context['columns'] = columns
        context['rows'] = rows
        if last_note == 0:
            context['lastnote'] = 0
        else:
            context['lastnote'] = last_note.pk
        
        return context


class ListDebates(ListView):
    """
    Return a list of debates for the current space.
    """
    paginate_by = 10
    
    def get_queryset(self):
        current_space = get_object_or_404(Space, url=self.kwargs['space_name'])
        debates = Debate.objects.all().filter(space=current_space)
        
        # Here must go a validation so a user registered to the space
        # can always see the debate list. While an anonymous or not
        # registered user can't see anything unless the space is public
        
        return debates
        
    def get_context_data(self, **kwargs):
        context = super(ListDebates, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context
