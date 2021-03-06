# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from django.db.models import Count
from django.forms import widgets
from cms.admin.placeholderadmin import PlaceholderAdminMixin

from django.utils.translation import ugettext_lazy as _

from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm
from aldryn_translation_tools.admin import AllTranslationsMixin
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from .models import Person, Group, Location

from .constants import (
    ALDRYN_PEOPLE_USER_THRESHOLD,
    ALDRYN_PEOPLE_HIDE_FAX,
    ALDRYN_PEOPLE_HIDE_WEBSITE,
    ALDRYN_PEOPLE_HIDE_FACEBOOK,
    ALDRYN_PEOPLE_HIDE_TWITTER,
    ALDRYN_PEOPLE_HIDE_LINKEDIN,
    ALDRYN_PEOPLE_HIDE_GROUPS,
    ALDRYN_PEOPLE_HIDE_LOCATION,
    ALDRYN_PEOPLE_HIDE_USER,
    ALDRYN_PEOPLE_SHOW_SECONDARY_IMAGE,
    ALDRYN_PEOPLE_SHOW_SECONDARY_PHONE,
    ALDRYN_PEOPLE_SUMMARY_RICHTEXT,
)

class PersonAdminForm(TranslatableModelForm):

    #class Meta:
        #model = Person

    def __init__(self, *args, **kwargs):
        super(PersonAdminForm, self).__init__(*args, **kwargs)
        if not ALDRYN_PEOPLE_SUMMARY_RICHTEXT:
            self.fields['description'].widget = widgets.Textarea()


class PersonAdmin(PlaceholderAdminMixin,
                  AllTranslationsMixin,
                  TranslatableAdmin):

    form = PersonAdminForm
    list_display = [
        '__str__', 'email', 'is_published', 'vcard_enabled', ]
    if ALDRYN_PEOPLE_HIDE_GROUPS == 0:
        list_display += ['num_groups',]
        list_filter = ['is_published', 'services', 'groups', 'vcard_enabled']
    else:
        list_filter = ['is_published', 'services', 'vcard_enabled']

    search_fields = ('translations__first_name', 'translations__last_name', 'email', 'translations__function')

    filter_horizontal = [
        'categories',
    ]

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """
        Determines if the User widget should be a drop-down or a raw ID field.
        """
        if ALDRYN_PEOPLE_HIDE_USER == 0:
            # This is a hack to use until get_raw_id_fields() lands in Django:
            # https://code.djangoproject.com/ticket/17881.
            if db_field.name in ['user', ]:
                model = Person._meta.get_field('user').model
                if model.objects.count() > ALDRYN_PEOPLE_USER_THRESHOLD:
                    kwargs['widget'] = admin.widgets.ForeignKeyRawIdWidget(
                        db_field.rel, self.admin_site, using=kwargs.get('using'))
                    return db_field.formfield(**kwargs)
        return super(PersonAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if ALDRYN_PEOPLE_HIDE_GROUPS == 0:
            if db_field.name == 'groups':
                kwargs['widget'] = SortedFilteredSelectMultiple()
        if db_field.name == 'services':
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super(PersonAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    contact_fields = (
        'visual',
    )
    if ALDRYN_PEOPLE_SHOW_SECONDARY_IMAGE != 0:
        contact_fields += (
            'second_visual',
        )
    contact_fields += (
        'email',
        'mobile',
        'phone',
    )
    if ALDRYN_PEOPLE_SHOW_SECONDARY_PHONE != 0:
        contact_fields += (
            'second_phone',
        )
    if ALDRYN_PEOPLE_HIDE_FAX == 0:
        contact_fields += (
            'fax',
        )
    if ALDRYN_PEOPLE_HIDE_WEBSITE == 0:
        contact_fields += (
            'website',
        )
    if ALDRYN_PEOPLE_HIDE_FACEBOOK == 0:
        contact_fields += (
            'facebook',
        )
    if ALDRYN_PEOPLE_HIDE_TWITTER == 0:
        contact_fields += (
            'twitter',
        )
    if ALDRYN_PEOPLE_HIDE_LINKEDIN == 0:
        contact_fields += (
            'linkedin',
        )
    if ALDRYN_PEOPLE_HIDE_LOCATION == 0:
        contact_fields += (
            'location',
        )
    contact_fields += (
        'vcard_enabled',
    )
    if ALDRYN_PEOPLE_HIDE_USER == 0:
        contact_fields += (
            'user',
        )

    fieldsets = (
        (None, {
            'fields': (
                'first_name',
                'last_name',
                'slug',
                'function', 'description', 'is_published',
            ),
        }),
        (_('Contact (untranslated)'), {
            'fields': contact_fields,
        }),
    )
    if ALDRYN_PEOPLE_HIDE_GROUPS == 0:
        fieldsets += ((None, {
            'fields': (
                'groups', 'categories', 'services',

            ),
        }),)
    else:
        fieldsets += ((None, {
            'fields': (
                'categories',
                'services',
            ),
        }),)

    def get_queryset(self, request):
        qs = super(PersonAdmin, self).get_queryset(request)
        qs = qs.annotate(group_count=Count('groups'))
        return qs

    def num_groups(self, obj):
        return obj.group_count
    num_groups.short_description = _('# Groups')
    num_groups.admin_order_field = 'group_count'


class GroupAdmin(PlaceholderAdminMixin,
                 AllTranslationsMixin,
                 TranslatableAdmin):

    list_display = ['__str__', 'city', 'num_people', ]
    search_filter = ['translations__name']
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'description',
            ),
        }),
        (_('Contact (untranslated)'), {
            'fields': (
                'phone',
                'fax',
                'email',
                'website',
                'address',
                'postal_code',
                'city'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super(GroupAdmin, self).get_queryset(request)
        qs = qs.annotate(people_count=Count('people'))
        return qs

    def num_people(self, obj):
        return obj.people_count
    num_people.short_description = _('# People')
    num_people.admin_order_field = 'people_count'


class LocationAdmin(PlaceholderAdminMixin,
                 AllTranslationsMixin,
                 TranslatableAdmin):
    list_display = ['__str__', 'office', 'city', 'is_published',]
    search_filter = ['translations__name', 'translations__office']
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'office',
                'is_published',
            ),
        }),
        (_('Contact (untranslated)'), {
            'fields': (
                'phone',
                'fax',
                'email',
                'website',
                'address',
                'postal_code',
                'city',
                'lat',
                'lng'
            )
        }),
    )


admin.site.register(Person, PersonAdmin)

if ALDRYN_PEOPLE_HIDE_GROUPS == 0:
    admin.site.register(Group, GroupAdmin)

if ALDRYN_PEOPLE_HIDE_LOCATION == 0:
    admin.site.register(Location, LocationAdmin)
