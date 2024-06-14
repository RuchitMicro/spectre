from django.shortcuts import render
from django.views import View

class IndexView(View):
    template_name = 'user/profile.html'

    def get(self, request, *args, **kwargs):
        context =   {

        }
        return render(request, self.template_name, context)

