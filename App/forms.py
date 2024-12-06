from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Please enter a valid email address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



from .models import Component , ComponentSubComponent , Stock , Order

class ComponentForm(forms.ModelForm):

    class Meta:
        model = Component
        fields = ['name', 'cost_per_unit', 'holding_cost', 'lead_time','order_cost', 'minimum_order_quantity', 'image']

class ComponentSubComponentForm(forms.ModelForm):
    class Meta:
        model = ComponentSubComponent
        fields = ['sub_component', 'quantity_needed']


# Création du formset pour les sous-composants
ComponentSubComponentFormSet = inlineformset_factory(
    Component,
    ComponentSubComponent,
    fk_name='parent_component',
    form=ComponentSubComponentForm,
    extra=4,  # Nombre de sous-composants supplémentaires vides pour commencer
    can_delete=True  # Permet la suppression d'une ligne de sous-composant
)

class StockUpdateForm(forms.ModelForm):
    component = forms.ModelChoiceField(queryset=Component.objects.all(), label="Composant")
    quantity_on_hand = forms.IntegerField(min_value=0, label="Quantité disponible")

    class Meta:
        model = Stock
        fields = ['component', 'quantity_on_hand']



class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['component', 'gross_requirements', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
        }