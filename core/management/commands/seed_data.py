from django.core.management.base import BaseCommand

from core.models import Toxicity, VaccineRule

VACCINES = [
    # species, vaccine, interval_days, boosters (None = repeats forever)
    ("caine", "Rabie", 365, None),
    ("caine", "Polivalent (DHPPi)", 365, None),
    ("caine", "Leptospiroză", 365, None),
    ("caine", "Tuse de canisă (Bordetella)", 365, None),
    ("pisica", "Rabie", 365, None),
    ("pisica", "Trivalent (FVRCP)", 365, None),
    ("pisica", "Leucemie felină (FeLV)", 365, None),
    ("iepure", "Mixomatoză + boala hemoragică (VHD)", 365, None),
]

# plant_name (latin/genus), common_name, species, level, note
D, P = "caine", "pisica"
TOXIC = [
    ("Epipremnum", "pothos", D, "mediu", "Iritații ale gurii, salivație, vărsături."),
    ("Epipremnum", "pothos", P, "mediu", "Iritații ale gurii, salivație, vărsături."),
    ("Monstera", "monstera", D, "mediu", "Cristale de oxalat: iritații ale gurii și gâtului."),
    ("Monstera", "monstera", P, "mediu", "Cristale de oxalat: iritații ale gurii și gâtului."),
    ("Philodendron", "philodendron", D, "mediu", "Cristale de oxalat: iritații, salivație."),
    ("Philodendron", "philodendron", P, "mediu", "Cristale de oxalat: iritații, salivație."),
    ("Dieffenbachia", "dieffenbachia", D, "ridicat", "Umflarea gurii și a gâtului, dificultăți la înghițit."),
    ("Dieffenbachia", "dieffenbachia", P, "ridicat", "Umflarea gurii și a gâtului, dificultăți la înghițit."),
    ("Lilium", "crin", P, "letal", "FOARTE periculos: poate cauza insuficiență renală acută la pisici."),
    ("Lilium", "crin", D, "usor", "Probleme digestive ușoare."),
    ("Hemerocallis", "crin de zi", P, "letal", "Poate cauza insuficiență renală la pisici."),
    ("Aloe", "aloe", D, "mediu", "Vărsături, diaree, letargie."),
    ("Aloe", "aloe", P, "mediu", "Vărsături, diaree, letargie."),
    ("Nerium oleander", "leandru", D, "letal", "Afectează inima; extrem de toxic."),
    ("Nerium oleander", "leandru", P, "letal", "Afectează inima; extrem de toxic."),
    ("Cycas revoluta", "palmier sago", D, "letal", "Toxic pentru ficat; foarte periculos."),
    ("Cycas revoluta", "palmier sago", P, "letal", "Toxic pentru ficat; foarte periculos."),
    ("Dracaena trifasciata", "limba soacrei", D, "usor", "Greață, vărsături."),
    ("Dracaena trifasciata", "limba soacrei", P, "usor", "Greață, vărsături."),
    ("Sansevieria", "limba soacrei", D, "usor", "Greață, vărsături."),
    ("Sansevieria", "limba soacrei", P, "usor", "Greață, vărsături."),
    ("Ficus benjamina", "ficus", D, "usor", "Iritații ale pielii și ale gurii."),
    ("Ficus benjamina", "ficus", P, "usor", "Iritații ale pielii și ale gurii."),
    ("Hedera", "iederă", D, "mediu", "Vărsături, salivație, diaree."),
    ("Hedera", "iederă", P, "mediu", "Vărsături, salivație, diaree."),
    ("Spathiphyllum", "crinul păcii", D, "mediu", "Cristale de oxalat: iritații ale gurii."),
    ("Spathiphyllum", "crinul păcii", P, "mediu", "Cristale de oxalat: iritații ale gurii."),
    ("Zamioculcas", "zamioculcas", D, "mediu", "Iritații ale gurii, vărsături."),
    ("Zamioculcas", "zamioculcas", P, "mediu", "Iritații ale gurii, vărsături."),
    ("Tulipa", "lalea", D, "mediu", "Bulbii sunt cei mai toxici."),
    ("Tulipa", "lalea", P, "mediu", "Bulbii sunt cei mai toxici."),
    ("Narcissus", "narcisă", D, "ridicat", "Vărsături, probleme cardiace; bulbii sunt cei mai toxici."),
    ("Narcissus", "narcisă", P, "ridicat", "Vărsături, probleme cardiace; bulbii sunt cei mai toxici."),
    ("Rhododendron", "azalee", D, "ridicat", "Salivație, vărsături, slăbiciune, probleme cardiace."),
    ("Rhododendron", "azalee", P, "ridicat", "Salivație, vărsături, slăbiciune, probleme cardiace."),
]


class Command(BaseCommand):
    help = "Load starter vaccine rules and plant toxicity list (safe to run many times)"

    def handle(self, *args, **opts):
        for sp, name, days, boost in VACCINES:
            VaccineRule.objects.get_or_create(
                species=sp, vaccine=name, defaults={"interval_days": days, "boosters": boost})
        for plant, common, sp, level, note in TOXIC:
            Toxicity.objects.get_or_create(
                plant_name=plant, pet_species=sp,
                defaults={"common_name": common, "level": level, "note": note})
        self.stdout.write("Seed data OK")
