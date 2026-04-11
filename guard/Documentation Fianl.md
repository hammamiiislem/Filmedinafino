Rapport d'Intégration : Système de Gestion des Partenaires
Cette documentation détaille les modifications apportées au backend pour permettre la gestion des partenaires et leur liaison avec les localisations géographiques via une API GraphQL.

1. Architecture des Données (Models)
Le système repose sur une relation Many-to-Many permettant à un partenaire de gérer plusieurs sites (locations) et vice-versa.

Page : guard/models.py
Deux classes principales ont été configurées :

Classe Partner : Représente l'entité commerciale.

name : Nom du partenaire.

email : Adresse unique pour la communication et la validation.

image : Logo traité avec un redimensionnement automatique (300x200).

is_verified : État de validation du compte.

locations : Relation ManyToManyField vers le modèle Location.

Classe Location : Représente le site physique.

Elle contient les informations géographiques (latitude, longitude) et les détails d'ouverture (openFrom, openTo).

2. Couche API (GraphQL Schema)
L'API a été développée avec Strawberry Django pour assurer une communication fluide et typée avec l'application mobile.

Page : api/schema.py
Les types GraphQL ont été définis pour mapper les modèles Django tout en respectant les conventions de nommage (camelCase).

PartnerType :

Mappe le champ is_verified du modèle vers isVerified dans l'API pour correspondre aux standards frontend.

Inclut un Resolver personnalisé pour le champ locations afin de garantir la récupération de la liste des sites associés :

Python
@strawberry.field
def locations(self, root) -> List["LocationType"]:
    return root.locations.all()
LocationType :

Définit la structure des données pour les sites, incluant le lien inverse vers le partenaire si nécessaire.

3. Documentation des Points de Terminaison (Queries)
Pour récupérer les données, une requête unique permet d'obtenir l'arborescence complète des partenaires et de leurs localisations respectives.

Test via GraphiQL Playground
Requête de sélection :

GraphQL
query GetPartnersWithLocations {
  partners {
    id
    name
    email
    isVerified
    image
    locations {
      id
      name
      latitude
      longitude
    }
  }
}
4. Journal des Corrections Techniques
Au cours du développement, plusieurs ajustements critiques ont été effectués pour stabiliser l'API :

Résolution du Naming Conflict : Correction de l'erreur FieldDoesNotExist en s'assurant que le field_name dans Strawberry correspond exactement au nom du champ dans le modèle Django (is_verified).

Gestion des Dépendances Circulaires : Utilisation de références sous forme de chaînes de caractères (ex: 'PartnerType') pour permettre aux classes de se référencer mutuellement sans erreur d'importation.

Correction du Cache Playground : Résolution des erreurs "Failed to fetch" en synchronisant l'état du serveur Django avec le schéma exposé dans l'interface GraphiQL.

5. État Final du Projet
Le backend est désormais prêt pour l'intégration mobile. Les données sont persistées en base de données, les images sont optimisées lors de l'upload, et l'API GraphQL expose une structure de données propre et documentée.