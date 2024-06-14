from django.shortcuts           import redirect, render,get_object_or_404
from django.views               import View     # Importing django class based view
from django.views.generic       import CreateView, TemplateView, ListView, UpdateView, DetailView # Importing django generic class based view
from django.http                import Http404

from web.models                 import *



class IndexView(TemplateView):
    template_name = "web/index.html"

class RedirectView(View):

    def get(self, request, slug, *args, **kwargs):
        redirect_url = get_object_or_404(Redirect, slug=slug)

        # Increment redirect count
        redirect_url.no_of_redirects    +=  1
        redirect_url.save()

        return redirect(str(redirect_url.target))


class BlogListView(ListView):
    model = Blog
    paginate_by = 12
    template_name   = "web/blog.html"
    ordering = ['order_by']

    def get_queryset(self, *args, **kwargs):
        qs = super(BlogListView, self).get_queryset()

        # If no slug is passed then set slug value as all
        try:
            if self.kwargs['slug']:
                pass
        except KeyError:
            self.kwargs['slug'] = 'all'


        try:
            BlogCategory.objects.get(slug=self.kwargs['slug'])
            pass
        except:
            raise Http404("Blog Category does not exist")

        if self.kwargs['slug']=='all':
            qs  =   qs
        else:
            qs  =   qs.filter(category__slug=self.kwargs['slug'])
            
        if self.request.GET.get('q'):
            qs  =   qs.filter(title__icontains=self.request.GET.get('q'))
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = BlogCategory.objects.get(slug=self.kwargs['slug'])
        context['all_category'] = BlogCategory.objects.all()
        context['settings'] = SiteSetting.objects.all().first()
        return context

class BlogDetailView(View):
    template_name = "web/blog-detail.html"

    def get(self, request, slug, *args, **kwargs):

        try:
            blog    =   Blog.objects.get(slug=slug)
            tags    =   [t for t in blog.tags.split(',')]   
        except Blog.DoesNotExist:
            raise Http404("Page not found")

        # contact_form    =   ContactForm()
        
        context =   {
            # 'contact_form': contact_form,
            'blog': blog,
            'tags': tags,
            'settings': SiteSetting.objects.all().first(),
        }

        return render(request, self.template_name, context)


def dashboard_callback(request, context):

    # if(closing.object.get(date=yesterday_date).exists()):
    # do nothing
    # else
    # incoming_money_total = get all incoming money of yesterday
    # outgoing_money_total = get all outgoing money of yesterday
    # yesterday_closing_balance = incoming_money_total - outgoing_money_total
    # total_balance = 
    # closing.object.create(date=yesterday_date, closing_balance=yesterday_closing_balance)


    context.update({
        "custom_variable": "value",
        "cards": [
            {"title": "Card 1", "metric": "Metric 1"},
            {"title": "Card 2", "metric": "Metric 2"},
            {"title": "Card 3", "metric": "Metric 3"},
        ],
        "navigation": [
            {"title": "Dashboard", "link": "/", "icon": "dashboard"},
            {"title": "Users", "link": "/admin/users", "icon": "people"},
        ],
        "filters": [
            {"title": "Filter 1", "link": "/filter1"},
            {"title": "Filter 2", "link": "/filter2"},
        ],
    })
    return context