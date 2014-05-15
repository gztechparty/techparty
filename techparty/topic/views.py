from django.shortcuts import render

from techparty.website.views import nav_menu


def topic_list_view(request):
    context = { }

    context = nav_menu(request,context)
    return render(request, 'about.html', context)