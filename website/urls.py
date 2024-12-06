"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from App.views import CustomLoginView , HomeView , SignUpView , ComponentCreateView,ComponentListView , create_component ,StockListView
from App.views import StockUpdateView , OrderCreateView , OrderListView , OrderUpdateView , ComponentUpdateView, OrderCreateView2 , component_hierarchy_view
from App.views import stock_evolution_view
from App.views import hierarchy_view , ComponentUpdateView2

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('home/', HomeView.as_view(), name='homepage'),
    path('add_component/', ComponentCreateView.as_view(), name='add_component'),
    path('component_list/', ComponentListView.as_view(), name='component_list'),
    path('create_component/', create_component, name='create_component'),
    path('components/update/<int:pk>/', ComponentUpdateView.as_view(), name='update_component'),
    path('components/update2/<int:pk>/', ComponentUpdateView2.as_view(), name='update_component2'),
    path('stocks/', StockListView.as_view(), name='stock_list'),
    path('stocks/update/<int:pk>/', StockUpdateView.as_view(), name='update_stock'),
    #path('orders/create/', OrderCreateView.as_view(), name='create_order'),
    path('orders/', OrderListView.as_view(), name='order_list'),  # URL pour afficher la liste des commandes
    path('orders/update/<int:pk>/', OrderUpdateView.as_view(), name='update_order'),  # URL pour modifier une commande
    path('orders/create/', OrderCreateView2.as_view(), name='create_order'),  # URL pour créer une commande avec un formulaire
    path('component/<int:component_id>/hierarchy/', component_hierarchy_view, name='component_hierarchy'),
    path('stock-evolution/', stock_evolution_view, name='stock_evolution'),
    path('hierarchy/', hierarchy_view, name='hierarchy'),

]

# Ajoutez ceci pour gérer les fichiers médias en développement

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
