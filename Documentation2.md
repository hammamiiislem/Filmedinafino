�Documentation Technique : Gestion des Partenaires & Validation Sécurisée
1. Présentation du Module:

Ce module permet l'enregistrement des partenaires (hôtels, musées, commerces) de la plateforme FielMedina. Il garantit la sécurité des données via un système de validation par e-mail et permet une
gestion flexible des localisations associées. 

2. Architecture de Données (Modèles):

Le système repose sur une relation Many-to-Many entre les Partenaires et les Localisations (Pointsd'intérêt). 
+Partner : Contient les informations de l'établissement (Nom, Email, Site Web, Logo). 
-is_verified (Boolean) : Indique si l'e-mail a été validé.
-locations (ManyToManyField) : Liste des circuits ou monuments associés. 
+Location : Représente les lieux physiques sur la carte FielMedina.
3. Flux de Travail (Workflow):

*1. Création : L'administrateur crée un partenaire via l'interface CRUD. 
*2. Génération de Token : Django génère un jeton (token) sécurisé via django.core.signing contenant l'ID du partenaire.
*3. Expédition : Un e-mail contenant un lien unique (/verify-email/?token=...) est envoyé au partenaire. 
*4. Validation : Lorsque le partenaire clique, le système décode le token, vérifie sa validité (48h)et passe is_verified à True.
4. Implémentation Technique:

A. Interface CRUD (Logic)

Nous utilisons une CreateView personnalisée pour gérer la sauvegarde des relations multiples. 
+Fonction clé : form_valid() 
+Action : Récupère les IDs des localisations cochées et les lie au partenaire après sa création. 

B. Sécurisation (Tokenization)

Au lieu d'utiliser des IDs simples dans l'URL (qui pourraient être piratés), nous utilisons des signatures
cryptographiques :
"Python"
token = signing.dumps({'partner_id': partner.id})

C. Interface Utilisateur (UI/UX)

+Checkboxes Grid : Utilisation de Tailwind CSS pour afficher les localisations sous forme de
grille (grid-cols-2) pour une meilleure lisibilité. 
+Flowbite Components : Intégration de composants modernes pour les formulaires et les messages de succès. 
5. Intégration API & GraphQL:

Pour permettre à l'application mobile (Android/iOS) d'afficher les partenaires, nous avons exposé le modèle via Graphene-Django.
+Query : allPartners 
+Filtre : Seuls les partenaires ayant is_verified=True sont visibles par le public. 
6. Guide de Test:
1. Étape 1 : Créer un partenaire via /staff/partners/create/.
2. Étape 2 : Récupérer le lien dans les logs du serveur (ou boîte mail).
3. Étape 3 : Ouvrir le lien dans le navigateur. 
4. Résultat attendu : Affichage de la page verification_success.html et mise à jour automatique de la base de données.