from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    # plants
    path("plante/", views.plant_list, name="plant_list"),
    path("plante/scan/", views.plant_scan, name="plant_scan"),
    path("plante/noua/", views.plant_new, name="plant_new"),
    path("plante/<int:pk>/", views.plant_detail, name="plant_detail"),
    path("plante/<int:pk>/sarcina/", views.plant_add_task, name="plant_add_task"),
    path("plante/<int:pk>/sterge/", views.plant_delete, name="plant_delete"),
    # pets
    path("animale/", views.pet_list, name="pet_list"),
    path("animale/nou/", views.pet_new, name="pet_new"),
    path("animale/identifica/", views.pet_identify, name="pet_identify"),
    path("animale/<int:pk>/editeaza/", views.pet_edit, name="pet_edit"),
    path("animale/<int:pk>/", views.pet_detail, name="pet_detail"),
    path("animale/<int:pk>/vaccin/", views.pet_add_vaccine, name="pet_add_vaccine"),
    path("animale/<int:pk>/sarcina/", views.pet_add_task, name="pet_add_task"),
    path("animale/<int:pk>/sterge/", views.pet_delete, name="pet_delete"),
    path("scan/<int:pk>/salveaza-animal/", views.scan_save_pet, name="scan_save_pet"),
    path("scan/<int:pk>/", views.scan_detail, name="scan_detail"),
    # tasks
    path("sarcini/<int:pk>/gata/", views.task_done, name="task_done"),
    path("sarcini/<int:pk>/sterge/", views.task_delete, name="task_delete"),
    # forum
    path("forum/", views.forum_list, name="forum_list"),
    path("forum/nou/", views.post_new, name="post_new"),
    path("forum/<int:pk>/", views.post_detail, name="post_detail"),
    path("forum/<int:pk>/vot/", views.post_vote, name="post_vote"),
    # push + PWA
    path("push/subscribe/", views.push_subscribe, name="push_subscribe"),
    path("push/test/", views.push_test, name="push_test"),
    path("sw.js", views.service_worker, name="sw"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
]
