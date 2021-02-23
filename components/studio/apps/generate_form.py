from django.shortcuts import render, HttpResponseRedirect, reverse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from django.template import engines
from .models import Apps, AppInstance, AppCategories, AppPermission, AppStatus
from projects.models import Project, Volume, Flavor, Environment
from models.models import Model
from projects.helpers import get_minio_keys
import modules.keycloak_lib as keylib
from .serialize import serialize_app
from .tasks import deploy_resource, delete_resource
import requests
import flatten_json
import uuid
from datetime import datetime, timedelta

key_words = ['appobj', 'model', 'flavor', 'environment', 'volumes', 'apps', 'logs', 'permissions', 'csrfmiddlewaretoken']

def get_form_models(aset, project, appinstance=[]):
    dep_model = False
    models = []
    if 'model' in aset:
        print('app requires a model')
        dep_model = True
        models = Model.objects.filter(project=project)
        
        for model in models:
            if appinstance and model.appinstance_set.filter(pk=appinstance.pk).exists():
                print(model)
                model.selected = "selected"
            else:
                model.selected = ""
    return dep_model, models

def get_form_apps(aset, project, myapp, user, appinstance=[]):
    dep_apps = False
    app_deps = []
    if 'apps' in aset:
        dep_apps = True
        app_deps = dict()
        apps = aset['apps']
        for app_name, option_type in apps.items():
            print(app_name)
            app_obj = Apps.objects.get(name=app_name)

            # TODO: Only get app instances that we have permission to list.
            app_instances = AppInstance.objects.filter(Q(owner=user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True), project=project, app=app_obj)
            # TODO: Special case here for "environment" app. Maybe fix, or maybe OK.
            # Could be solved by supporting "condition": '"appobj.app_slug":"true"'
            if app_name == "Environment":
                key = 'appobj'+'.'+myapp.slug

                app_instances = AppInstance.objects.filter(Q(owner=user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True),
                                                           project=project,
                                                           app=app_obj,
                                                           parameters__contains={
                                                               "appobj": {
                                                                    myapp.slug: True
                                                                }
                                                           })
            
            for ain in app_instances:
                if appinstance and ain.appinstance_set.filter(pk=appinstance.pk).exists():
                    ain.selected = "selected"
                else:
                    ain.selected = ""

            if option_type == "one":
                app_deps[app_name] = {"instances": app_instances, "option_type": ""}
            else:
                app_deps[app_name] = {"instances": app_instances, "option_type": "multiple"}
    return dep_apps, app_deps

def get_form_primitives(aset, project, appinstance=[]):
    all_keys = aset.keys()
    print("PRIMITIVES")
    primitives = dict()
    if appinstance:
        ai_vals = flatten_json.flatten(appinstance.parameters, '.')
    for key in all_keys:
        if key not in key_words:
            primitives[key] = aset[key]
            if appinstance:
                for subkey, subval in aset[key].items():
                    primitives[key][subkey]['default'] = ai_vals[key+'.'+subkey]
    print(primitives)
    return primitives

def get_form_permission(aset, project, appinstance=[]):
    form_permissions = {
        "public": {"value":"false", "option": "false"},
        "project": {"value":"false", "option": "false"},
        "private": {"value":"true", "option": "true"}
    }
    dep_permissions = True
    if 'permissions' in aset:
        form_permissions = aset['permissions']
        # if not form_permissions:
        #     dep_permissions = False

        if appinstance:
            try:
                ai_vals = eval(appinstance.parameters)
                form_permissions['public']['value'] = ai_vals['permissions.public']
                form_permissions['project']['value'] = ai_vals['permissions.project']
                form_permissions['private']['value'] = ai_vals['permissions.private']
            except:
                print("Permissions not set for app instance, using default.")
    return dep_permissions, form_permissions

def get_form_appobj(aset, project, appinstance=[]):
    print("CHECKING APP OBJ")
    dep_appobj = False
    appobjs = dict()
    if 'appobj' in aset:
        print("NEEDS APP OBJ")
        dep_appobj = True
        appobjs['objs'] = Apps.objects.all()
        appobjs['title'] = aset['appobj']['title']
        appobjs['type'] = aset['appobj']['type']

    print(appobjs)
    return dep_appobj, appobjs


def generate_form(aset, project, app, user, appinstance=[]):
    form = dict()
    form['dep_model'], form['models'] = get_form_models(aset, project, appinstance)
    form['dep_apps'], form['app_deps'] = get_form_apps(aset, project, app, user, appinstance)
    form['dep_appobj'], form['appobjs'] = get_form_appobj(aset, project, appinstance)

    form['dep_vols'] = False
    form['dep_flavor'] = False
    if 'flavor' in aset:
        form['dep_flavor'] = True
        form['flavors'] = Flavor.objects.all()
    
    form['dep_environment'] = False
    if 'environment' in aset:
        form['dep_environment'] = True
        form['environments'] = Environment.objects.all()


    form['primitives'] = get_form_primitives(aset, project, appinstance)
    form['dep_permissions'], form['form_permissions'] = get_form_permission(aset, project, appinstance)
    return form