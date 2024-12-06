from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.views.generic import CreateView, ListView , UpdateView , View
from .forms import SignUpForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect , get_object_or_404
from .forms import ComponentForm , ComponentSubComponentForm , ComponentSubComponentFormSet , StockUpdateForm , OrderForm
from .models import Component , ComponentSubComponent , Stock , Order
from django.utils import timezone
from django.db.models import OuterRef, Subquery
from .models import generate_hierarchy_graph , generate_hierarchy_for_component
from django.http import Http404
class CustomLoginView(LoginView):
    template_name = 'login.html'  # Votre fichier de template pour la page de login
    next_page = reverse_lazy('homepage')  # Redirection après login


class HomeView(TemplateView):
    template_name = 'home.html'  # Spécifiez le template que la vue doit utiliser


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'signup.html'
    success_url = reverse_lazy('homepage')  # Redirection après inscription réussie

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)  # Connecte automatiquement l'utilisateur après l'inscription
        return response


# Vue pour créer un composant
class ComponentCreateView(CreateView):
    model = Component
    form_class = ComponentForm
    template_name = 'create_component.html'
    success_url = reverse_lazy('component_list')  # Redirige vers la liste des composants après création

    # Méthode GET pour afficher le formulaire de création de composant
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['sub_component_formset'] = ComponentSubComponentFormSet(self.request.POST, instance=self.object)
        else:
            data['sub_component_formset'] = ComponentSubComponentFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        sub_component_formset = context['sub_component_formset']

        # Vérifier que les deux formulaires sont valides avant d'enregistrer
        if form.is_valid() and sub_component_formset.is_valid():
            # Enregistrer le composant principal
            self.object = form.save()

            # Définir l'attribut `parent_component` pour chaque sous-composant du formset
            sub_component_formset.instance = self.object
            for sub_form in sub_component_formset:
                sub_form.instance.parent_component = self.object  # Assigner le parent_component

            # Enregistrer le formset
            sub_component_formset.save()
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)


class ComponentUpdateView2(View):
    """
    Vue pour mettre à jour un composant, y compris ses sous-composants.
    """
    def get(self, request, pk):
        component = get_object_or_404(Component, pk=pk)
        form = ComponentForm(instance=component)
        formset = ComponentSubComponentFormSet(instance=component)  # Préremplit le formset avec les sous-composants
        return render(request, 'component_update2.html', {
            'form': form,
            'formset': formset,
            'component': component
        })

    def post(self, request, pk):
        component = get_object_or_404(Component, pk=pk)
        form = ComponentForm(request.POST, request.FILES, instance=component)
        formset = ComponentSubComponentFormSet(request.POST, instance=component)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()  # Sauvegarde des sous-composants
            return redirect('component_list')

        return render(request, 'component_update2.html', {
            'form': form,
            'formset': formset,
            'component': component
        })


# Vue pour afficher la liste des composants
class ComponentListView(ListView):
    model = Component
    template_name = 'component_list.html'
    context_object_name = 'components'  # Nom du contexte pour accéder aux composants dans le template

    # Méthode POST pour gérer la suppression d'un composant
    def post(self, request, *args, **kwargs):
        component_id = request.POST.get("component_id")
        Component.objects.filter(id=component_id).delete()
        return redirect('component_list')



def component_hierarchy_view(request, component_id):
    """
    Vue pour afficher la hiérarchie des sous-composants d'un composant donné.
    """
    component = get_object_or_404(Component, id=component_id)

    # Génération de l'image de la hiérarchie
    image_url = component.generate_component_hierarchy()

    return render(request, 'component_hierarchy.html', {
        'component': component,
        'image_url': image_url
    })


def create_component(request):
    if request.method == "POST":
        component_form = ComponentForm(request.POST, request.FILES)
        formset = ComponentSubComponentFormSet(request.POST, instance=Component())

        if component_form.is_valid() and formset.is_valid():
            component = component_form.save()
            formset.instance = component
            formset.save()
            return redirect('component_list')  # Redirige vers la liste des composants après création
    else:
        component_form = ComponentForm()
        formset = ComponentSubComponentFormSet(instance=Component())

    return render(request, 'create_component_2.html', {
        'component_form': component_form,
        'formset': formset
    })

def hierarchy_view(request):
    try:
        # Filtrer uniquement le composant "skate"
        skate_component = Component.objects.get(name="Skate")
    except Component.DoesNotExist:
        raise Http404("Composant 'skate' introuvable.")

        # Générer l'organigramme pour le composant skate
    figure_json = generate_hierarchy_for_component(skate_component.id)

    return render(request, 'hierarchy.html', {
        'figure_json': figure_json,
        'component_name': skate_component.name
    })
class ComponentUpdateView(UpdateView):
    model = Component
    form_class = ComponentForm
    template_name = 'component_update.html'
    success_url = reverse_lazy('component_list')  # Redirection après la modification


class StockListView(ListView):
    model = Stock
    template_name = 'stock_list.html'  # Template pour afficher la liste
    context_object_name = 'stocks'  # Nom de la variable à utiliser dans le template

    def get_queryset(self):
        today = now().date()

        # Parcourir tous les composants
        for component in Component.objects.all():
            # Vérifier si un enregistrement pour le stock existe aujourd'hui
            if not Stock.objects.filter(component=component, date=today).exists():
                # Récupérer le dernier stock enregistré pour ce composant
                latest_stock = Stock.objects.filter(component=component).order_by('-date').first()
                if latest_stock:
                    # Créer un nouvel enregistrement de stock basé sur le dernier état connu
                    Stock.objects.create(
                        component=component,
                        quantity_on_hand=latest_stock.quantity_on_hand,
                        date=today
                    )
                else:
                    # Si aucun stock n'existe, initialiser avec une quantité de 0
                    Stock.objects.create(
                        component=component,
                        quantity_on_hand=0,
                        date=today
                    )

        # Retourner les stocks pour la date d'aujourd'hui
        return Stock.objects.filter(date=today)


class StockUpdateView(UpdateView):
    model = Stock
    form_class = StockUpdateForm
    template_name = 'update_stock.html'
    success_url = reverse_lazy('stock_list')  # Redirige vers la liste des stocks après la mise à jour

    def get_object(self, queryset=None):
        # Récupère ou crée un enregistrement de stock pour le composant sélectionné à la date actuelle
        component_id = self.kwargs['pk']
        today = timezone.now().date()
        stock, created = Stock.objects.get_or_create(
            component_id=component_id,
            date=today,
            defaults={'quantity_on_hand': 0}  # Quantité initiale si l'enregistrement est nouveau
        )
        return stock

def stock_evolution_view(request):
    """
    Affiche l'évolution des stocks pour un composant sélectionné via un sélecteur.
    """
    # Récupérer tous les composants pour le sélecteur
    components = Component.objects.all()

    # Récupérer le composant sélectionné (par défaut, le premier composant)
    component_id = request.GET.get('component_id', components.first().id if components.exists() else None)
    component = get_object_or_404(Component, id=component_id) if component_id else None

    # Générer les données pour le graphique
    stock_chart = component.generate_interactive_stock_chart() if component else None

    return render(request, 'stock_evolution.html', {
        'components': components,
        'selected_component': component,
        'stock_chart': stock_chart,
    })


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'create_order.html'
    success_url = reverse_lazy('order_list')  # Redirige après la création vers une liste des commandes


class OrderCreateView2(View):
    """
    Vue permettant de créer une commande avec un formulaire
    et de calculer dynamiquement la date limite pour le composant sélectionné.
    """

    def get(self, request):
        # Charger le formulaire de commande
        order_form = OrderForm()
        return render(request, 'order_create_d.html', {'order_form': order_form})

    def post(self, request):
        if 'component_id' in request.POST:
            # Traitement AJAX pour calculer la date limite
            component_id = request.POST.get('component_id')

            if not component_id:
                return JsonResponse({'error': 'Invalid data'}, status=400)

            try:
                component = Component.objects.get(id=component_id)
                deadline = now()+timedelta(weeks=component.calculate_order_deadline_2())
                numbers_of_weeks = component.calculate_order_deadline_2()
                image_url = component.image.url if component.image else None
                return JsonResponse(
                    {'deadline': deadline.strftime('%Y-%m-%d'),
                     'numbers_of_weeks': numbers_of_weeks,
                     'image_url': image_url
                     })
            except Component.DoesNotExist:
                return JsonResponse({'error': 'Component not found'}, status=404)
        else:
            # Traitement du formulaire de commande
            order_form = OrderForm(request.POST)
            if order_form.is_valid():
                order = order_form.save(commit=False)
                component = order.component
                deadline = now() + timedelta(weeks=component.calculate_order_deadline_2())

                # Validation : vérifier que la date de commande est après la date limite
                if order.order_date < deadline.date():
                    order_form.add_error('order_date',
                                         f"La date de commande ne peut pas être antérieure à {deadline.strftime('%d-%m-%Y')}.")
                else:
                    order.save()
                    return redirect('order_list')  # Redirection après soumission réussie
            # Réafficher le formulaire avec les erreurs en cas de problème
            return render(request, 'order_create_d.html', {'order_form': order_form})

class OrderListView(View):
    def get(self, request):
        # Récupérer les commandes groupées par composant
        orders = Order.objects.select_related('component', 'stock').all()

        # Organiser les commandes par composant
        orders_by_component = {}
        for order in orders:
            component = order.component
            if component not in orders_by_component:
                orders_by_component[component] = []
            orders_by_component[component].append(order)

        # Récupérer les commandes pour les gross requirements des skates
        skateboard_component = Component.objects.filter(name="Skate").first()
        gross_requirements = Order.objects.filter(component=skateboard_component)

        return render(request, 'order_list.html', {
            'orders_by_component': orders_by_component,
            'gross_requirements': gross_requirements,
        })

    def post(self, request):
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order.delete_with_dependencies()  # Suppression avec dépendances
        except Order.DoesNotExist:
            pass
        return redirect('order_list')


class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'update_order.html'
    success_url = reverse_lazy('order_list')