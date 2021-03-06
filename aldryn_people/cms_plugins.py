# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import defaultdict

from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from aldryn_people import models, forms, DEFAULT_APP_NAMESPACE
from .utils import get_valid_languages


NAMESPACE_ERROR = _(
    "Seems that there is no valid application hook for aldryn-people."
    "Links can't be rendered without an app hook."
)


class PeoplePlugin(CMSPluginBase):

    TEMPLATE_NAME = 'aldryn_people/plugins/%s/people_list.html'
    module = 'People'
    render_template = TEMPLATE_NAME % models.PeoplePlugin.STYLE_CHOICES[0][0]
    name = _('People list')
    model = models.PeoplePlugin

    fieldsets = (
        (None, {
            'fields': (
                'style',
            ),
        }),
        (_('People'), {
            'description': _('Select and arrange specific people, or leave '
                             'blank to use all.'),
            'fields': (
                'people',
            )
        }),
        (_('Options'), {
            'fields': (
                ('group_by_group', 'show_ungrouped', ),
                'show_links',
                'show_vcard',
            )
        })
    )

    def group_people(self, people):
        groups = defaultdict(list)

        for person in people:
            for group in person.groups.all():
                groups[group].append(person)

        # Fixes a template resolution-related issue. See:
        # http://stackoverflow.com/questions/4764110/django-template-cant-loop-defaultdict  # noqa
        groups.default_factory = None
        return groups

    def render(self, context, instance, placeholder):
        people = instance.get_selected_people()
        if not people:
            people = models.Person.objects.published()
        valid_languages = get_valid_languages(
            DEFAULT_APP_NAMESPACE, instance.language, context['request'])
        people = people.translated(*valid_languages)
        if not valid_languages:
            context['namespace_error'] = NAMESPACE_ERROR
        self.render_template = self.TEMPLATE_NAME % instance.style

        context['instance'] = instance
        context['people'] = people

        if instance.group_by_group:
            context['people_groups'] = self.group_people(people)
            if instance.show_ungrouped:
                groupless = people.filter(groups__isnull=True)
            else:
                groupless = people.none()
            context['groupless_people'] = groupless
        else:
            context['people_groups'] = []
            context['groupless_people'] = people.none()
        return context


plugin_pool.register_plugin(PeoplePlugin)


@plugin_pool.register_plugin
class RelatedPeoplePlugin(CMSPluginBase):
    TEMPLATE_NAME = 'aldryn_people/plugins/related_people__%s.html'
    module = 'People'
    render_template = TEMPLATE_NAME % forms.LAYOUT_CHOICES[0][0]
    name = _('Related People')
    model = models.RelatedPeoplePlugin
    form = forms.RelatedPeoplePluginForm

    def render(self, context, instance, placeholder):
        request = context.get('request')
        context['instance'] = instance
        context['title'] = instance.title
        context['icon'] = instance.icon
        context['image'] = instance.image

        qs = instance.related_people.published()
        related_groups = instance.related_groups.all()
        related_locations = instance.related_locations.all()
        related_categories = instance.related_categories.all()
        related_services = instance.related_services.all()

        if not qs.exists():
            qs = models.Person.objects.published().distinct()
            if related_groups.exists():
                qs = qs.filter(groups__in=related_groups)
            if related_locations.exists():
                qs = qs.filter(location__in=related_locations)
            if related_categories.exists():
                qs = qs.filter(categories__in=related_categories)
            if related_services.exists():
                qs = qs.filter(services__in=related_services)

        context['related_people'] = qs[:int(instance.number_of_people)]

        return context

    def get_render_template(self, context, instance, placeholder):
        return self.TEMPLATE_NAME % instance.layout
