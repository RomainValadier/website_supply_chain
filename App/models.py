from django.db import models

from django.db import models
from django.utils import timezone
from datetime import timedelta , date
import math
from django.core.exceptions import ValidationError
import matplotlib.pyplot as plt
import networkx as nx
from io import BytesIO
import plotly.graph_objects as go
from pyvis.network import Network
import os
from django.conf import settings

class Skate_order(models.Model):
    date_order = models.DateField()  # Semaine de la commande
    production_quantity = models.IntegerField()  # Quantité de skates à produire par semaine


class Component(models.Model):
    name = models.CharField(max_length=100) # Nom du composant
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    holding_cost= models.DecimalField(max_digits=10, decimal_places=2)  # Coût de possession par unité
    order_cost = models.DecimalField(max_digits=10, decimal_places=2)  # Coût de commande
    lead_time = models.IntegerField()  # Délai de livraison en semaines
    minimum_order_quantity = models.IntegerField()  # Quantité minimale de commande
    image = models.ImageField(upload_to='components/', blank=True, null=True)  # Champ pour l'image
    # Définir une relation intermédiaire pour les sous-composants
    sub_components = models.ManyToManyField(
        'self',
        through='ComponentSubComponent',
        symmetrical=False,
        related_name='parent_components',
        blank=True # Permet de ne pas renseigner de sous-composants lors de la création
    )

    def __str__(self):
        return self.name

    def clean(self):
        # Validation : Vérifie que les coûts et les quantités sont positifs
        if self.cost_per_unit < 0:
            raise ValidationError("Le coût par unité ne peut pas être négatif.")
        if self.holding_cost < 0:
            raise ValidationError("Le coût de possession ne peut pas être négatif.")
        if self.order_cost < 0:
            raise ValidationError("Le coût de commande ne peut pas être négatif.")
        if self.lead_time < 0:
            raise ValidationError("Le délai de livraison (lead time) ne peut pas être négatif.")
        if self.minimum_order_quantity < 1:
            raise ValidationError("La quantité minimale de commande doit être au moins 1.")

    def save(self, *args, **kwargs):
        # Valider les données avant de sauvegarder
        self.clean()

        # Appel à la méthode save du modèle parent
        super().save(*args, **kwargs)
        # Crée un objet Stock avec quantité initiale 0 si aucun stock n'existe pour ce composant
        if not Stock.objects.filter(component=self).exists():
            Stock.objects.create(component=self, quantity_on_hand=0, date=timezone.now())

    def get_all_subcomponents(self):
        """
        Retourne une liste de tous les sous-composants liés directement ou indirectement.
        Utile pour vérifier les dépendances.
        """
        subcomponents = []
        for relation in ComponentSubComponent.objects.filter(parent_component=self):
            subcomponents.append(relation.sub_component)
            subcomponents.extend(relation.sub_component.get_all_subcomponents())
        return subcomponents



    def calculate_order_deadline_2(self,deadline=0,level=0):
        sub_components = self.get_all_subcomponents()
        if(len(sub_components) == 0):
            return self.lead_time
        else:
            max_leadtime = 0
            max_subcomponent = None
            for sub_component in sub_components :
                sub_component_lead_time= sub_component.lead_time
                if(sub_component_lead_time > max_leadtime):
                    max_leadtime = sub_component_lead_time
                    max_subcomponent = sub_component
        print(level,max_subcomponent, max_leadtime)
        return self.lead_time+max_subcomponent.calculate_order_deadline_2(max_leadtime,level+1)



    def generate_interactive_stock_chart(self):
        """
        Génère un graphique interactif Plotly montrant l'évolution des stocks.
        Retourne le graphique sous forme JSON.
        """
        # Récupérer les données de stock
        stocks = Stock.objects.filter(component=self).order_by('date')

        if not stocks.exists():
            return None

        # Préparer les données
        dates = [stock.date for stock in stocks]
        quantities = [stock.quantity_on_hand for stock in stocks]

        # Créer le graphique Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=quantities,
            mode='lines+markers',
            name='Quantité en Stock',
            line=dict(color='blue')
        ))

        fig.update_layout(
            title=f"Évolution des Stocks pour {self.name}",
            xaxis_title="Date",
            yaxis=dict(
                title="Quantité en stock",
                range=[0, max(quantities)*1.2]
            ),
            template="plotly_white"

        )

        # Retourner le graphique au format JSON
        return fig.to_json()


def generate_hierarchy_for_component(component_id):
    """
    Génère un organigramme hiérarchique Plotly pour un composant spécifique et ses sous-composants,
    en incluant les quantités associées dans les cercles.
    """
    try:
        root_component = Component.objects.get(id=component_id)
    except Component.DoesNotExist:
        return None  # Retourne None si le composant n'existe pas

    # Préparer les nœuds et les relations
    nodes = []
    edges = []

    def traverse(component, level=0, position=0, parent_id=None):
        """
        Parcours récursif pour collecter les relations parent-enfant et les quantités associées.
        """
        # Ajouter un nœud avec la quantité associée
        subcomponents = Component.sub_components.through.objects.filter(parent_component=component)
        label = f"{component.name}"

        if parent_id:
            # Ajouter une relation parent-enfant
            relation = Component.sub_components.through.objects.filter(
                parent_component_id=parent_id.split('-')[0], sub_component=component).first()
            quantity = relation.quantity_needed if relation else 0
            label += f"\n({quantity})"

        node_id = f"{component.id}-{level}-{position}"  # ID unique pour gérer les doublons

        nodes.append({
            "id": node_id,
            "label": label,
            "level": level,
            "position": position
        })

        if parent_id:
            edges.append((parent_id, node_id))

        # Parcourir les sous-composants
        for i, relation in enumerate(subcomponents):
            child = relation.sub_component
            traverse(child, level + 1, position + i - len(subcomponents) // 2, parent_id=node_id)

    # Commencer avec le composant racine
    traverse(root_component)

    # Préparer les coordonnées pour Plotly
    x_coords = []
    y_coords = []
    labels = []

    node_positions = {}
    for node in nodes:
        x_coords.append(node["position"])
        y_coords.append(-node["level"])  # Inverser Y pour que la racine soit en haut
        labels.append(node["label"])
        node_positions[node["id"]] = (node["position"], -node["level"])

    # Ajouter les liens (arêtes)
    edge_x = []
    edge_y = []

    for parent_id, child_id in edges:
        parent_x, parent_y = node_positions[parent_id]
        child_x, child_y = node_positions[child_id]

        edge_x.extend([parent_x, child_x, None])
        edge_y.extend([parent_y, child_y, None])

    # Tracer le graphique avec Plotly
    fig = go.Figure()

    # Ajouter les liens (arêtes)
    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(color="gray", width=2),
        hoverinfo="none"
    ))

    # Ajouter les nœuds (points)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode="markers+text",
        marker=dict(size=40, color="lightblue", line=dict(color="blue", width=2)),
        text=labels,
        textposition="top center"
    ))

    # Configurer la mise en page
    fig.update_layout(
        title=f"Hiérarchie pour {root_component.name} ",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=50, l=25, r=25, b=25),
        plot_bgcolor="white"
    )

    return fig.to_json()


def generate_hierarchy_graph():
    # Initialisation
    net = Network(height="750px", width="100%", directed=True)

    # Charger les composants
    components = Component.objects.all()

    # Ajouter les nœuds avec images
    for component in components:
        image_path = component.image.url if component.image else None
        if image_path:
            net.add_node(
                component.id,
                label=component.name,
                shape="image",
                image=os.path.join(settings.MEDIA_URL, component.image.name),
            )
            print(f"Added node {component.name} with image {image_path}")
        else:
            net.add_node(
                component.id,
                label=component.name,
                shape="circle",  # Utilisez un cercle par défaut si pas d'image
            )

    # Ajouter les relations parent-enfant
    for relation in Component.sub_components.through.objects.all():
        net.add_edge(relation.parent_component_id, relation.sub_component_id)

    # Sauvegarder le graphe interactif
    try:
        output_path = os.path.join(settings.MEDIA_ROOT, "component_hierarchy.html")
        net.show(output_path)
        print(f"Graph saved at {output_path}")
        return os.path.join(settings.MEDIA_URL, "component_hierarchy.html")
    except Exception as e:
        print(f"Erreur lors du rendu du graphe : {e}")
        return None


class ComponentSubComponent(models.Model):
    parent_component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='parent_component')
    sub_component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='used_in_components')
    quantity_needed = models.IntegerField()  # Quantité de sous-composant nécessaire pour fabriquer le composant principal

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parent_component', 'sub_component'], name='unique_subcomponent_for_component')
        ]


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Stock(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity_on_hand = models.IntegerField()
    date = models.DateField(default=timezone.now)

    def adjust_stock(self, quantity_needed, net_requirement,order_release):
        """
        Ajuste le stock en fonction du gross_requirement.
        Si la demande est supérieure au stock disponible, met le stock à 0.
        Sinon, réduit le stock par quantity_needed.
        """
        if quantity_needed >= self.quantity_on_hand:
            self.quantity_on_hand = 0
        else:
            self.quantity_on_hand -= quantity_needed
            # Vérifie si la commande dépasse le net_requirement
        if order_release > net_requirement:
            surplus = order_release - net_requirement
            self.quantity_on_hand += surplus  # Ajouter le surplus au stock

        self.save()  # Enregistrer les changements


class Order(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    order_date = models.DateField()
    gross_requirements = models.IntegerField()
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    net_requirement = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    order_release_date = models.DateField(editable=False)  # Calculée automatiquement lors de l'enregistrement
    planned_order_receipt = models.IntegerField(editable=False)

    def clean(self):
        # Vérifie que la date de commande n'est pas dans le passé
        if self.order_date < date.today():
            raise ValidationError("La date de commande ne peut pas être antérieure à aujourd'hui.")

    def save(self, *args, **kwargs):
        self.clean()
        # Calcul des valeurs automatiques

        self.order_release_date = self.order_date - timedelta(weeks=self.component.lead_time)

        # Récupérer le dernier état de stock pour ce composant
        # Récupérer l'objet stock à la date de la commande

        latest_stock = Stock.objects.filter(component=self.component, date__lt=self.order_date).order_by(
            '-date').first()
        self.net_requirement = max(0, self.gross_requirements - latest_stock.quantity_on_hand)
        self.planned_order_receipt = math.ceil(
            self.net_requirement / self.component.minimum_order_quantity) * self.component.minimum_order_quantity
        self.cost = self.component.order_cost + (self.net_requirement * self.component.cost_per_unit)

        stock_obj = Stock.objects.filter(component=self.component, date=self.order_date).first()

        if not stock_obj:
            # Récupérer le dernier état de stock pour ce composant avant la date de la commande

            if latest_stock:
                # Créer un nouvel objet stock basé sur le dernier état connu
                stock_obj = Stock.objects.create(
                    component=self.component,
                    quantity_on_hand=latest_stock.quantity_on_hand,
                    date=self.order_date
                )
                stock_obj.adjust_stock(self.gross_requirements,self.net_requirement,self.planned_order_receipt)
            else:
                # Si aucun stock n'existe, initialiser avec une quantité de 0
                stock_obj = Stock.objects.create(
                    component=self.component,
                    quantity_on_hand=0,
                    date=self.order_date
                )


        self.stock = stock_obj  # Associer l'objet stock

        """
        # Ajuster le stock à J+1
        next_day = self.order_date + timedelta(days=1)
        next_day_stock = Stock.objects.filter(component=self.component, date=next_day).first()

        if not next_day_stock:
            # Créer un stock à J+1 si inexistant
            next_day_stock = Stock.objects.create(
                component=self.component,
                quantity_on_hand=stock_obj.quantity_on_hand,  # Reprend la quantité du jour précédent
                date=next_day
            )

        # Ajuster le stock à J+1
        next_day_stock.adjust_stock(self.gross_requirements)
        """

        super(Order, self).save(*args, **kwargs)

        if(self.net_requirement > 0 and self.component.sub_components is not None):

            for subcomponent_relation in self.component.sub_components.through.objects.filter(
                    parent_component=self.component):
                subcomponent = subcomponent_relation.sub_component
                quantity_needed = subcomponent_relation.quantity_needed
                print("Subcomponent: ", subcomponent, "Quantity needed: ", quantity_needed)
                print(self.planned_order_receipt)

                # Calcul des besoins bruts pour le sous-composant
                subcomponent_gross_requirements = self.planned_order_receipt * quantity_needed

                # Créer une commande pour le sous-composant
                sub_order = Order(
                    component=subcomponent,
                    order_date=self.order_release_date,
                    gross_requirements=subcomponent_gross_requirements
                )
                sub_order.save()

    def delete_with_dependencies(self):
        """
        Supprime cette commande ainsi que toutes ses dépendances :
        - Mises à jour du stock associées.
        - Commandes des sous-composants associées à la bonne date.
        """
        # Récupérer la date de commande associée
        order_date_subcomponents = self.order_release_date

        # Récupérer les sous-composants associés
        sub_components = self.component.sub_components.all()

        # Supprimer les commandes des sous-composants à la bonne date
        associated_orders = Order.objects.filter(
            component__in=sub_components,
            order_date=order_date_subcomponents
        )
        if(associated_orders is not None):
            for order in associated_orders:
                order.delete_with_dependencies()
        # Supprimer les mises à jour de stock associées à cette commande
        Stock.objects.filter(component=self.component, date=self.order_date).delete()

        # Supprimer la commande actuelle
        super(Order, self).delete()


