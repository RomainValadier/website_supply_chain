// Fonction de connexion
function loginUser() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    if (email && password) {
        window.location.href = "order.html";
        return false; // Empêche le rechargement de la page
    } else {
        alert("Veuillez entrer un email et un mot de passe.");
        return false;
    }
}

// Fonction pour soumettre la commande
function submitOrder() {
    const quantity = document.getElementById("quantity").value;
    const destination = document.getElementById("destination").value;
    const dateTime = document.getElementById("dateTime").value;

    if (quantity && destination && dateTime) {
        window.location.href = "details.html";
        return false;
    } else {
        alert("Veuillez remplir tous les champs.");
        return false;
    }
}

// Retour à la page de commande
function goBackToOrder() {
    window.location.href = "order.html";
}

// Données pour chaque composant (valeurs par défaut)
const componentData = {
    "Trucks": { annualDemand: 60000, purchaseCost: 20, holdingCostRate: 5, orderingCost: 65, image: "images/trucks.jpg" },
    "Board": { annualDemand: 30000, purchaseCost: 0, holdingCostRate: 15, orderingCost: 100, image: "images/board.jpeg" },
    "Wheels": { annualDemand: 120000, purchaseCost: 0, holdingCostRate: 2, orderingCost: 10, image: "images/wheels.jpg" },
    "Tire": { annualDemand: 120000, purchaseCost: 1, holdingCostRate: 0.5, orderingCost: 15, image: "images/tire.jpg" },
    "Screws": { annualDemand: 720000, purchaseCost: 0.1, holdingCostRate: 0.01, orderingCost: 5, image: "images/screws.jpg" },
    "Rim": { annualDemand: 120000, purchaseCost: 2, holdingCostRate: 1, orderingCost: 30, image: "images/rim.jpg" }
};

// Fonction pour mettre à jour les informations en fonction du composant sélectionné
function updateComponentInfo() {
    const component = document.getElementById("componentSelect").value;
    const components = JSON.parse(localStorage.getItem('componentData')) || componentData;
    const data = components[component];

    if (data) {
        // Calculs spécifiques
        const EOQ = Math.sqrt((2 * data.annualDemand * data.orderingCost) / (data.purchaseCost * data.holdingCostRate)).toFixed(2);
        const numOrders = (data.annualDemand / EOQ).toFixed(2);
        const workingDays = 200;
        const timeBetweenOrders = (workingDays / numOrders).toFixed(2);

        // Mise à jour des informations dans le tableau
        document.getElementById("annualDemand").textContent = data.annualDemand;
        document.getElementById("purchaseCost").textContent = data.purchaseCost;
        document.getElementById("holdingCost").textContent = (data.holdingCostRate * 100).toFixed(2);
        document.getElementById("orderingCost").textContent = data.orderingCost;
        document.getElementById("EOQ").textContent = EOQ;
        document.getElementById("numOrders").textContent = numOrders;
        document.getElementById("timeBetweenOrders").textContent = timeBetweenOrders;

        // Mise à jour de l'image du composant
        const componentImage = document.getElementById("componentImage");
        componentImage.src = data.image;
        componentImage.alt = `Image of ${component}`;
    }
}

// Soumettre un nouveau composant via formulaire
function submitNewComponent(event) {
    event.preventDefault(); // Empêche le rafraîchissement de la page lors de la soumission du formulaire

    // Récupérer les valeurs des champs du formulaire
    const name = document.getElementById("componentName").value;
    const annualDemand = parseInt(document.getElementById("annualDemand").value);
    const purchaseCost = parseFloat(document.getElementById("purchaseCost").value);
    const holdingCostRate = parseFloat(document.getElementById("holdingCostRate").value);
    const orderingCost = parseFloat(document.getElementById("orderingCost").value);

    // Appel à la fonction d'ajout de composant
    addNewComponent(name, annualDemand, purchaseCost, holdingCostRate, orderingCost);
}

// Ajouter un composant à l'objet componentData et le stocker dans localStorage
function addNewComponent(name, annualDemand, purchaseCost, holdingCostRate, orderingCost) {
    // Définir le chemin par défaut pour l'image des nouveaux composants
    const defaultImagePath = "images/default_component.jpg";

    // Ajouter les données du nouveau composant
    componentData[name] = {
        annualDemand: annualDemand,
        purchaseCost: purchaseCost,
        holdingCostRate: holdingCostRate,
        orderingCost: orderingCost,
        image: defaultImagePath // Image par défaut
    };

    // Mettre à jour le menu déroulant pour inclure le nouveau composant
    const componentSelect = document.getElementById("componentSelect");
    if (componentSelect) {
        const option = document.createElement("option");
        option.value = name;
        option.text = name;
        componentSelect.appendChild(option);
    }

    // Sauvegarder les données des composants dans localStorage
    localStorage.setItem("componentData", JSON.stringify(componentData));

    alert(`Component ${name} added successfully!`);
    window.location.href = "order.html"; // Rediriger vers la page de commande
}

// Fonction pour charger les composants et afficher dans le menu déroulant
function populateComponentSelect() {
    const componentSelect = document.getElementById("componentSelect");
    const components = JSON.parse(localStorage.getItem('componentData')) || componentData;

    // Effacer les options existantes
    componentSelect.innerHTML = '';

    // Ajouter les options pour chaque composant
    for (const name in components) {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        componentSelect.appendChild(option);
    }

    // Mettre à jour les informations pour le composant sélectionné
    updateComponentInfo();
}

// Charger les informations par défaut et peupler le menu déroulant au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
    const componentSelect = document.getElementById("componentSelect");
    if (componentSelect) {
        componentSelect.addEventListener("change", updateComponentInfo);
        populateComponentSelect(); // Charger les composants du localStorage
    }
});
