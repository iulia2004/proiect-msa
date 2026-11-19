import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import ai, push
from .forms import (CommentForm, PetForm, PetScanForm, PlantForm, PlantScanForm, PostForm, SaveIdentifiedPetForm, TaskForm, VaccineForm)
from .image_utils import prepare_photo
from .models import (PET_KINDS, PLANT_KINDS, CareTask, Pet, Plant, PushSubscription, Scan, Toxicity, Vote, Post)


# ---------- home / login ----------
def login_page(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "login.html")


@login_required
def home(request):
    today = timezone.localdate()
    base = CareTask.objects.filter(owner=request.user, active=True).select_related("plant", "pet")
    due = base.filter(next_due__lte=today)
    soon = base.filter(next_due__gt=today, next_due__lte=today + timedelta(days=7))
    return render(request, "home.html", {
        "due": due, "soon": soon,
        "plant_count": Plant.objects.filter(owner=request.user).count(),
        "pet_count": Pet.objects.filter(owner=request.user).count(),
    })


# ---------- plants ----------
def toxic_alerts(plant, pets):
    text = f"{plant.species} {plant.common_name}".lower().strip()
    if not text or not pets:
        return []
    out = []
    for t in Toxicity.objects.filter(pet_species__in={p.species for p in pets}):
        if t.plant_name.lower() in text or (t.common_name and t.common_name.lower() in text):
            out += [(p, t) for p in pets if p.species == t.pet_species]
    return out


@login_required
def plant_list(request):
    return render(request, "plants/list.html", {"plants": Plant.objects.filter(owner=request.user)})


@login_required
def plant_scan(request):
    form = PlantScanForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        plant = form.save(commit=False)
        plant.owner = request.user
        photo_name, photo_content = prepare_photo(form.cleaned_data["photo"])
        plant.photo.save(photo_name, photo_content, save=False)
        plant.save()
        cands = ai.identify(plant.photo.path, "plant")
        top = cands[0] if cands else {}
        plant.species = top.get("species", "")
        plant.common_name = top.get("common_name", "")
        if not plant.name:
            plant.name = plant.common_name or plant.species or "Plantă nouă"
        plant.save()
        rep = ai.diagnose_plant(plant.photo.path, plant.species, plant.common_name)
        Scan.objects.create(
            owner=request.user, kind="plant", image=plant.photo.name, plant=plant,
            species=plant.species, common_name=plant.common_name, score=top.get("score", 0),
            candidates=cands, health=rep["health"], diagnosis=rep["diagnosis"],
            advice=rep["advice"], confidence=rep["confidence"],
        )
        today = timezone.localdate()
        for kind, title, days in (("udat", "Udat", 7), ("fertilizat", "Fertilizat", 30)):
            CareTask.objects.create(
                owner=request.user, plant=plant, kind=kind, title=title,
                frequency_days=days, next_due=today + timedelta(days=days),
            )
        if toxic_alerts(plant, list(request.user.pets.all())):
            messages.warning(request, "⚠️ Atenție: planta aceasta este toxică pentru unul dintre animalele tale!")
        return redirect("plant_detail", plant.pk)
    return render(request, "form.html", {
        "title": "Scanează o plantă 🌿", "form": form, "multipart": True, "wait": True,
        "submit": "Analizează planta",
    })


@login_required
def plant_new(request):
    form = PlantForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        plant = form.save(commit=False)
        plant.owner = request.user
        photo = form.cleaned_data["photo"]
        if photo:
            photo_name, photo_content = prepare_photo(photo)
            plant.photo.save(photo_name, photo_content, save=False)
        plant.save()
        today = timezone.localdate()
        CareTask.objects.create(
            owner=request.user,
            plant=plant,
            kind="udat",
            title="Udat",
            frequency_days=7,
            next_due=today + timedelta(days=7),
        )
        if toxic_alerts(plant, list(request.user.pets.all())):
            messages.warning(request, "⚠️ Atenție: planta aceasta poate fi toxică pentru unul dintre animalele tale!")
        return redirect("plant_detail", plant.pk)
    return render(request, "form.html", {
        "title": "Adaugă o plantă",
        "form": form,
        "multipart": True,
        "submit": "Salvează planta",
    })


@login_required
def plant_detail(request, pk):
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)
    return render(request, "plants/detail.html", {
        "plant": plant,
        "scan": plant.scans.first(),
        "alerts": toxic_alerts(plant, list(request.user.pets.all())),
        "tasks": plant.tasks.filter(active=True),
        "task_form": TaskForm(kinds=PLANT_KINDS),
    })


def _add_task(request, target, kinds, back):
    form = TaskForm(request.POST, kinds=kinds)
    if form.is_valid():
        t = form.save(commit=False)
        t.owner = request.user
        for k, v in target.items():
            setattr(t, k, v)
        if not t.title:
            t.title = t.get_kind_display()
        t.save()
    else:
        messages.error(request, "Completează corect formularul.")
    return redirect(back)


@login_required
@require_POST
def plant_add_task(request, pk):
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)
    return _add_task(request, {"plant": plant}, PLANT_KINDS, plant)


@login_required
@require_POST
def plant_delete(request, pk):
    get_object_or_404(Plant, pk=pk, owner=request.user).delete()
    return redirect("plant_list")


# ---------- pets ----------
@login_required
def pet_list(request):
    return render(request, "pets/list.html", {"pets": Pet.objects.filter(owner=request.user)})


@login_required
def pet_new(request):
    form = PetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        pet = form.save(commit=False)
        pet.owner = request.user
        pet.save()
        return redirect("pet_detail", pet.pk)
    return render(request, "form.html", {"title": "Adaugă un animal 🐾", "form": form, "submit": "Salvează"})


@login_required
def pet_edit(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    form = PetForm(request.POST or None, instance=pet)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("pet_detail", pet.pk)
    return render(request, "form.html", {
        "title": f"Editează profilul lui {pet.name}",
        "form": form,
        "submit": "Salvează modificările",
    })


@login_required
def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    return render(request, "pets/detail.html", {
        "pet": pet,
        "photo_scan": pet.scans.first(),
        "tasks": pet.tasks.filter(active=True),
        "vaccine_form": VaccineForm(pet),
        "task_form": TaskForm(kinds=PET_KINDS),
    })


@login_required
@require_POST
def pet_add_vaccine(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    form = VaccineForm(pet, request.POST)
    if form.is_valid():
        rule, given = form.cleaned_data["rule"], form.cleaned_data["given_on"]
        CareTask.objects.create(
            owner=request.user, pet=pet, kind="vaccin", title=rule.vaccine,
            frequency_days=rule.interval_days, next_due=given + timedelta(days=rule.interval_days),
            last_done=given, doses_left=rule.boosters,
        )
    else:
        messages.error(request, "Alege un vaccin și o dată validă.")
    return redirect(pet)


@login_required
@require_POST
def pet_add_task(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    return _add_task(request, {"pet": pet}, PET_KINDS, pet)


@login_required
@require_POST
def pet_delete(request, pk):
    get_object_or_404(Pet, pk=pk, owner=request.user).delete()
    return redirect("pet_list")


@login_required
def pet_identify(request):
    form = PetScanForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        photo_name, photo_content = prepare_photo(form.cleaned_data["photo"])
        scan = Scan(owner=request.user, kind="animal")
        scan.image.save(photo_name, photo_content, save=False)
        scan.save()
        cands = ai.identify(scan.image.path, "animal")
        top = cands[0] if cands else {}
        rep = ai.pet_advice(scan.image.path, top.get("species", ""), top.get("common_name", ""))
        scan.species, scan.common_name, scan.score = top.get("species", ""), top.get("common_name", ""), top.get("score", 0)
        scan.candidates = cands
        scan.health, scan.diagnosis, scan.advice, scan.confidence = (
            rep["health"], rep["diagnosis"], rep["advice"], rep["confidence"])
        scan.save()
        return redirect("scan_detail", scan.pk)
    return render(request, "form.html", {
        "title": "Identifică un animal 🔍", "form": form, "multipart": True, "wait": True,
        "submit": "Identifică",
    })


@login_required
def scan_detail(request, pk):
    scan = get_object_or_404(Scan, pk=pk, owner=request.user, kind="animal")
    initial = {
        "name": scan.common_name or scan.species or "Animal nou",
        "species": _pet_species_from_identification(scan.common_name),
        "location": "interior",
    }
    return render(request, "scan_detail.html", {
        "scan": scan,
        "save_pet_form": SaveIdentifiedPetForm(initial=initial),
    })


def _pet_species_from_identification(common_name):
    name = common_name.casefold()
    if "câine" in name:
        return "caine"
    if "pisic" in name:
        return "pisica"
    if "iepure" in name:
        return "iepure"
    if "hamster" in name:
        return "hamster"
    if any(bird in name for bird in ("peruș", "nimf", "canar", "papagal")):
        return "pasare"
    return "altul"


@login_required
@require_POST
def scan_save_pet(request, pk):
    scan = get_object_or_404(Scan, pk=pk, owner=request.user, kind="animal")
    if scan.pet_id:
        return redirect(scan.pet)

    form = SaveIdentifiedPetForm(request.POST)
    if form.is_valid():
        pet = Pet.objects.create(
            owner=request.user,
            name=form.cleaned_data["name"],
            species=form.cleaned_data["species"],
            location=form.cleaned_data["location"],
        )
        scan.pet = pet
        scan.save(update_fields=["pet"])
        return redirect(pet)

    return render(request, "scan_detail.html", {"scan": scan, "save_pet_form": form})


# ---------- tasks ----------
@login_required
@require_POST
def task_done(request, pk):
    get_object_or_404(CareTask, pk=pk, owner=request.user).mark_done()
    return HttpResponse("", headers={"HX-Refresh": "true"})


@login_required
@require_POST
def task_delete(request, pk):
    get_object_or_404(CareTask, pk=pk, owner=request.user).delete()
    return HttpResponse("", headers={"HX-Refresh": "true"})


# ---------- forum ----------
@login_required
def forum_list(request):
    cat = request.GET.get("c", "")
    qs = Post.objects.filter(is_hidden=False).select_related("author").annotate(
        vote_count=Count("votes", distinct=True),
        comment_count=Count("comments", filter=Q(comments__is_hidden=False), distinct=True),
    )
    if cat in ("plante", "animale"):
        qs = qs.filter(category=cat)
    posts = list(qs[:100])
    voted = set(Vote.objects.filter(user=request.user, post__in=posts).values_list("post_id", flat=True))
    for p in posts:
        p.voted = p.pk in voted
    return render(request, "forum/list.html", {"posts": posts, "cat": cat})


@login_required
def post_new(request):
    form = PostForm(request.POST or None, initial={"category": request.GET.get("c", "plante")})
    if request.method == "POST" and form.is_valid():
        ok, why = ai.moderate(form.cleaned_data["title"] + "\n" + form.cleaned_data["body"])
        if ok:
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(post)
        messages.error(request, f"Mesajul a fost respins de moderare. {why}")
    return render(request, "form.html", {"title": "Postare nouă", "form": form, "submit": "Publică", "wait": True})


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, is_hidden=False)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ok, why = ai.moderate(form.cleaned_data["body"])
        if ok:
            c = form.save(commit=False)
            c.post, c.author = post, request.user
            c.save()
            return redirect(post)
        messages.error(request, f"Comentariul a fost respins de moderare. {why}")
    return render(request, "forum/detail.html", {
        "post": post, "form": form,
        "comments": post.comments.filter(is_hidden=False).select_related("author"),
        "count": post.votes.count(),
        "voted": post.votes.filter(user=request.user).exists(),
    })


@login_required
@require_POST
def post_vote(request, pk):
    post = get_object_or_404(Post, pk=pk, is_hidden=False)
    vote, created = Vote.objects.get_or_create(user=request.user, post=post)
    if not created:
        vote.delete()
    return render(request, "_vote.html", {"post": post, "count": post.votes.count(), "voted": created})


# ---------- push + PWA ----------
@login_required
@require_POST
def push_subscribe(request):
    try:
        data = json.loads(request.body)
        endpoint, keys = data["endpoint"], data["keys"]
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh": keys["p256dh"], "auth": keys["auth"]},
        )
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def push_test(request):
    n = push.send_to_user(request.user, "Flauna 🌿", "Notificările funcționează!", "/")
    if n:
        messages.success(request, "Notificare trimisă. Ar trebui să o primești în câteva secunde.")
    else:
        messages.error(request, "Nu am putut trimite. Apasă mai întâi „Activează notificările” și verifică cheile VAPID din .env.")
    return redirect("home")


def service_worker(request):
    js = (settings.BASE_DIR / "core" / "static" / "sw.js").read_text()
    return HttpResponse(js, content_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


def manifest(request):
    return JsonResponse({
        "name": "Flauna",
        "short_name": "Flauna",
        "description": "Îngrijire pentru plante și animale de companie",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f6f7f1",
        "theme_color": "#214b3b",
        "icons": [
            {"src": static("icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": static("icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }, content_type="application/manifest+json")
