from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

User = settings.AUTH_USER_MODEL

PET_SPECIES = [
    ("caine", "Câine"),
    ("pisica", "Pisică"),
    ("iepure", "Iepure"),
    ("hamster", "Hamster"),
    ("pasare", "Pasăre"),
    ("altul", "Altul"),
]
PET_LOCATIONS = [
    ("interior", "Interior"),
    ("exterior", "Exterior"),
    ("ambele", "Interior și exterior"),
]

TASK_KINDS = [
    ("udat", "Udat"),
    ("fertilizat", "Fertilizat"),
    ("schimb_pamant", "Schimbat pământul"),
    ("vaccin", "Vaccin"),
    ("deparazitare", "Deparazitare"),
    ("hranire", "Hrănire"),
]
PLANT_KINDS = [k for k in TASK_KINDS if k[0] in ("udat", "fertilizat", "schimb_pamant")]
PET_KINDS = [k for k in TASK_KINDS if k[0] in ("hranire", "deparazitare")]


class Plant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plants")
    name = models.CharField("Nume", max_length=120, blank=True)
    species = models.CharField(max_length=200, blank=True)
    common_name = models.CharField(max_length=200, blank=True)
    photo = models.ImageField("Poză", upload_to="plants/", blank=True)
    location = models.CharField(
        "Unde stă planta", max_length=10,
        choices=[("interior", "Interior"), ("exterior", "Exterior")], default="interior",
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name or self.common_name or self.species or "Plantă"

    def get_absolute_url(self):
        return reverse("plant_detail", args=[self.pk])


class Pet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField("Nume", max_length=120)
    species = models.CharField("Specie", max_length=20, choices=PET_SPECIES, default="caine")
    breed = models.CharField("Rasă", max_length=120, blank=True)
    location = models.CharField(
        "Unde stă animalul", max_length=10, choices=PET_LOCATIONS, default="interior",
    )
    birth_date = models.DateField("Data nașterii", null=True, blank=True)
    weight_kg = models.DecimalField("Greutate (kg)", max_digits=6, decimal_places=2, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("pet_detail", args=[self.pk])


class CareTask(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    plant = models.ForeignKey(Plant, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks")
    pet = models.ForeignKey(Pet, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks")
    kind = models.CharField("Tip", max_length=20, choices=TASK_KINDS)
    title = models.CharField("Titlu", max_length=150, blank=True)
    frequency_days = models.PositiveIntegerField("Repetă la (zile)", null=True, blank=True)
    next_due = models.DateField("Următoarea dată", default=timezone.localdate)
    last_done = models.DateField(null=True, blank=True)
    doses_left = models.PositiveIntegerField(null=True, blank=True)  # None = repeats forever
    active = models.BooleanField(default=True)
    last_notified = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["next_due"]

    @property
    def target_name(self):
        t = self.plant or self.pet
        return str(t) if t else ""

    def mark_done(self):
        today = timezone.localdate()
        self.last_done = today
        if self.doses_left is not None:
            self.doses_left -= 1
            if self.doses_left <= 0:
                self.active = False
        if self.frequency_days and self.active:
            self.next_due = today + timedelta(days=self.frequency_days)
        elif not self.frequency_days:
            self.active = False
        self.save()


class VaccineRule(models.Model):
    species = models.CharField(max_length=20, choices=PET_SPECIES)
    vaccine = models.CharField(max_length=120)
    interval_days = models.PositiveIntegerField("Interval până la următoarea doză (zile)")
    boosters = models.PositiveIntegerField("Număr de rapeluri (gol = se repetă mereu)", null=True, blank=True)

    class Meta:
        unique_together = ("species", "vaccine")

    def __str__(self):
        return f"{self.get_species_display()} – {self.vaccine}"


class Toxicity(models.Model):
    LEVELS = [("usor", "Ușoară"), ("mediu", "Medie"), ("ridicat", "Ridicată"), ("letal", "Letală")]
    plant_name = models.CharField("Plantă (nume latin / gen)", max_length=150)
    common_name = models.CharField("Nume popular", max_length=150, blank=True)
    pet_species = models.CharField(max_length=20, choices=PET_SPECIES)
    level = models.CharField(max_length=10, choices=LEVELS, default="mediu")
    note = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name_plural = "toxicity"

    def __str__(self):
        return f"{self.plant_name} → {self.get_pet_species_display()}"


class Scan(models.Model):
    KINDS = [("plant", "Plantă"), ("animal", "Animal")]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    kind = models.CharField(max_length=10, choices=KINDS)
    image = models.ImageField(upload_to="scans/")
    plant = models.ForeignKey(Plant, null=True, blank=True, on_delete=models.SET_NULL, related_name="scans")
    pet = models.ForeignKey(Pet, null=True, blank=True, on_delete=models.SET_NULL, related_name="scans")
    species = models.CharField(max_length=200, blank=True)
    common_name = models.CharField(max_length=200, blank=True)
    score = models.FloatField(default=0)
    candidates = models.JSONField(default=list, blank=True)
    health = models.CharField(max_length=200, blank=True)
    diagnosis = models.TextField(blank=True)
    advice = models.TextField(blank=True)
    confidence = models.CharField(max_length=50, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class Post(models.Model):
    CATEGORIES = [("plante", "Plante"), ("animale", "Animale")]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category = models.CharField("Categorie", max_length=10, choices=CATEGORIES)
    title = models.CharField("Titlu", max_length=200)
    body = models.TextField("Mesaj")
    is_hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.pk])


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField("Comentariu")
    is_hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created"]


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="votes")

    class Meta:
        unique_together = ("user", "post")


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
