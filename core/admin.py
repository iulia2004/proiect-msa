from django.contrib import admin

from . import models


@admin.register(models.VaccineRule)
class VaccineRuleAdmin(admin.ModelAdmin):
    list_display = ("species", "vaccine", "interval_days", "boosters")
    list_filter = ("species",)


@admin.register(models.Toxicity)
class ToxicityAdmin(admin.ModelAdmin):
    list_display = ("plant_name", "common_name", "pet_species", "level")
    list_filter = ("pet_species", "level")
    search_fields = ("plant_name", "common_name")


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "is_hidden", "created")
    list_filter = ("category", "is_hidden")
    actions = ["hide", "unhide"]

    @admin.action(description="Ascunde postările selectate")
    def hide(self, request, qs):
        qs.update(is_hidden=True)

    @admin.action(description="Arată postările selectate")
    def unhide(self, request, qs):
        qs.update(is_hidden=False)


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "is_hidden", "created")
    list_filter = ("is_hidden",)


admin.site.register([models.Plant, models.Pet, models.CareTask, models.Scan, models.PushSubscription])
