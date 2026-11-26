from allauth.account.forms import LoginForm, SignupForm
from django import forms
from django.utils import timezone

from .models import PET_LOCATIONS, PET_SPECIES, CareTask, Pet, Plant, Post, Comment, VaccineRule

INPUT = "w-full rounded-lg border border-stone-300 bg-white px-3 py-2"
DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
PHOTO = forms.FileInput(attrs={"accept": "image/*"})


class Styled:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"] = INPUT


class PlantScanForm(Styled, forms.ModelForm):
    class Meta:
        model = Plant
        fields = ["photo", "name", "location"]
        widgets = {"photo": PHOTO}
        labels = {"name": "Nume (opțional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = True


class PlantForm(Styled, forms.ModelForm):
    class Meta:
        model = Plant
        fields = ["name", "common_name", "species", "location", "photo"]
        widgets = {"photo": PHOTO}
        labels = {
            "name": "Numele plantei",
            "common_name": "Nume popular",
            "species": "Specie (opțional)",
            "photo": "Fotografie (opțională)",
        }


class PetScanForm(Styled, forms.Form):
    photo = forms.ImageField(label="Poză cu animalul", widget=PHOTO)


class PetForm(Styled, forms.ModelForm):
    class Meta:
        model = Pet
        fields = ["name", "species", "breed", "location", "birth_date", "weight_kg"]
        widgets = {"birth_date": DATE}
        labels = {"name": "Numele animalului"}


class SaveIdentifiedPetForm(Styled, forms.Form):
    name = forms.CharField(label="Numele animalului", max_length=120)
    species = forms.ChoiceField(label="Specie", choices=PET_SPECIES)
    location = forms.ChoiceField(label="Unde stă animalul", choices=PET_LOCATIONS)


class VaccineForm(Styled, forms.Form):
    rule = forms.ModelChoiceField(queryset=VaccineRule.objects.none(), label="Vaccin")
    given_on = forms.DateField(label="Data administrării", widget=DATE, initial=timezone.localdate)

    def __init__(self, pet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rule"].queryset = VaccineRule.objects.filter(species=pet.species)


class TaskForm(Styled, forms.ModelForm):
    class Meta:
        model = CareTask
        fields = ["kind", "title", "frequency_days", "next_due"]
        widgets = {"next_due": DATE}
        labels = {"frequency_days": "Repetă la fiecare (zile)"}
        help_texts = {
            "frequency_days": "Opțional: 1 = zilnic, 7 = săptămânal. După ce marchezi reminderul ca făcut, se programează din nou automat. Lasă necompletat pentru o singură dată."
        }

    def __init__(self, *args, kinds=None, **kwargs):
        super().__init__(*args, **kwargs)
        if kinds:
            self.fields["kind"].choices = kinds
        self.fields["title"].required = False
        self.fields["frequency_days"].required = False
        self.fields["frequency_days"].min_value = 1
        self.fields["frequency_days"].widget.attrs.update({
            "min": "1",
            "step": "1",
            "placeholder": "ex. 1 pentru zilnic",
        })


class PostForm(Styled, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["category", "title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class CommentForm(Styled, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}
        labels = {"body": "Scrie un comentariu"}


# --- allauth forms with proper Romanian labels ---

AUTH_LABELS = {
    "login": ("Email sau nume de utilizator", "adresa@exemplu.ro sau utilizator"),
    "email": ("Email", "adresa@exemplu.ro"),
    "username": ("Nume de utilizator", "Alege un nume de utilizator"),
    "password": ("Parolă", "Parola ta"),
    "password1": ("Parolă", "Alege o parolă"),
    "password2": ("Confirmă parola", "Scrie parola din nou"),
    "remember": ("Ține-mă minte", None),
}


class AuthLabels:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for name, (label, placeholder) in AUTH_LABELS.items():
            if name in self.fields:
                self.fields[name].label = label
                if placeholder:
                    self.fields[name].widget.attrs["placeholder"] = placeholder


class FlaunaLoginForm(AuthLabels, LoginForm):
    pass


class FlaunaSignupForm(AuthLabels, SignupForm):
    pass
