import click
import prettytable

from .main import main
from .stackn import (call_admin_endpoint, call_project_endpoint, get_current,
                     get_projects, get_remote)


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


def _print_table(resource, names, keys):
    x = prettytable.PrettyTable()
    x.field_names = names
    for item in resource:
        row = [item[k] for k in keys]
        x.add_row(row)
    print(x)


def _find_dict_by_value(dicts, key, value):
    try:
        res = next(item for item in dicts if item[key] == value)
    except Exception as e:
        print(f"Object type {value} doesn't exist.")
        return []
    return res


@main.group('get', cls=AliasedGroup)
def get():
    pass


@get.command('app')
@click.option('-c', '--category', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def app(category, secure):
    params = {"app__category": category.lower()} if category else []
    apps = call_project_endpoint('appinstances', params=params, conf={
                                 "STACKN_SECURE": secure})

    # call_project_endpoint can return false for various reasons
    if apps == False:
        print("Apps could not be fetched.")
        return False
    elif len(apps) == 0:
        print("There are no apps associated with the current project.")
        return

    applist = []
    for app in apps:
        status = max(app['status'], key=lambda x: x['id'])
        tmp = {
            'name': app['name'],
            'app_name': app['app']['name'],
            'app_cat': app['app']['category']['name'],
            'url': '',
            'state': app['state'],
            'status': status['status_type'],
        }
        if 'url' in app['table_field']:
            tmp['url'] = app['table_field']['url']
        applist.append(tmp)
    applist = sorted(applist, key=lambda k: k['app_cat'])

    _print_table(applist, ['Category', 'App', 'Name', 'URL', 'Status'], [
                 'app_cat', 'app_name', 'name', 'url', 'status'])


@get.command('current')
@click.option('--secure/--insecure', required=False, default=True)
def get_curr(secure):

    if not (current := get_current(secure=secure)):
        return False
    if current['STACKN_URL']:
        print(f"Studio: {current['STACKN_URL']}")
        if current['STACKN_PROJECT']:
            print(f"Project: {current['STACKN_PROJECT']}")
        else:
            print("No project set.")


@get.command('environment')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def environment(project, studio_url, secure):

    conf = {
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }

    environments = call_project_endpoint('environments', conf=conf)

    if environments == False:
        return False
    elif len(environments) == 0:
        print("There are no environments associated with the current project")
        return

    envlist = []
    for env in environments:
        tmp = {
            'name': env['name'],
            'app_name': env['app']['name'],
            'cat': env['app']['category']['name'],
            'image': env['repository'] + '/' + env['image'],
        }
        envlist.append(tmp)
    header = ['Category', 'App', 'Name', 'Image']
    fields = ['cat', 'app_name', 'name', 'image']
    envlist = sorted(envlist, key=lambda k: k['cat'])

    _print_table(envlist, header, fields)


@get.command('flavor')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def flavor(project, studio_url, secure):

    conf = {
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }

    flavors = call_project_endpoint('flavors', conf=conf)

    if flavors == False:
        return False
    elif len(flavors) == 0:
        print("No flavors are associated to the current project.")
        return

    header = ['Name', 'CPU req', 'CPU lim', 'Mem req',
              'Mem lim', 'GPUs', 'Eph mem req', 'Eph mem lim']
    fields = ['name', 'cpu_req', 'cpu_lim', 'mem_req',
              'mem_lim', 'gpu_req', 'ephmem_req', 'ephmem_lim']

    _print_table(flavors, header, fields)


@get.command('mlflow')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def mlflow(project, studio_url, secure):

    conf = {
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }

    mlflows = call_project_endpoint('mlflow', conf=conf)

    if mlflows == False:
        return False
    elif len(mlflows) == 0:
        print("No MLflows endpoints are associated to the current project.")
        return

    mlflowlist = []
    for mlflow in mlflows:
        tmp = {
            'name': mlflow['name'],
            'URL': mlflow['mlflow_url'],
            'S3': mlflow['s3']['name'],
        }
        mlflowlist.append(tmp)

    _print_table(mlflowlist, ['Name', 'URL', 'S3'], ['name', 'URL', 'S3'])


@get.command('model-obj')
@click.option('-t', '--object-type', required=False, default="model")
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def obj(object_type, project, studio_url, secure):

    conf = {
        'STACKN_OBJECT_TYPE': object_type,
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }

    object_types = call_project_endpoint('objecttypes', conf=conf)

    if object_types == False:
        return False

    obj_type = _find_dict_by_value(object_types, 'slug', object_type)

    if not obj_type:
        print("No model objects found for this project.")
        return

    params = {'object_type': obj_type['id']}

    objects = call_project_endpoint('models', conf=conf, params=params)

    if objects == False:
        return False
    elif len(objects) == 0:
        print("No model objects are associated to the current project.")
        return

    obj_dict = {str(obj_type['id']): obj_type['name'] for obj_type in object_types}
    for obj in objects:
        obj['object_type'] = obj_dict[str(obj['object_type'][0])]

    _print_table(objects, ['Name', 'Version', 'Type', 'Created'], [
                 'name', 'version', 'object_type', 'uploaded_at'])


@get.command('project')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def project(studio_url, secure):

    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }

    projects = get_projects(conf=conf)

    if projects == False:
        return False
    elif len(projects) == 0:
        print("There are no projects associated to the current user.")
        return

    _print_table(projects, ['Name', 'Created'], ['name', 'created_at'])


@get.command('project-templates')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def templates(studio_url, secure):
    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }
    templates = call_admin_endpoint('project_templates', conf=conf)

    # call_admin_endpoint can return false for various reasons
    if templates == False:
        print("Templates could not be fetched.")
        return False
    elif len(templates) == 0:
        print("There are no templates.")
        return

    templateslist = []
    for template in templates:
        tmp = {'name': template['name'], 'description': template['description']}
        templateslist.append(tmp)

    _print_table(templateslist, ['Name', 'Description'], [
                 'name', 'description'])


@get.command('remote')
@click.option('--secure/--insecure', required=False, default=True)
def get_rem(secure):

    if not (current_remote := get_remote(inp_conf={'STACKN_SECURE': secure})):
        return False
    for curr in current_remote:
        print(curr)


@get.command('s3')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-n', '--name', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
def s3(project, studio_url, name, secure):
    conf = {
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }
    params = {"name": name} if name else []
    s3s = call_project_endpoint('s3', params=params, conf=conf)

    if s3s == False:
        return False
    elif len(s3s) == 0:
        print("There are no S3 endpoints associated with the current project.")
        return
    else:
        _print_table(s3s, ['Name', 'Host', 'Region'],
                     ['name', 'host', 'region'])


ALIASES = {
    "projects": project,
    "proj": project,
    "template": templates,
    "tmpl": templates,
    "apps": app,
    "objects": obj,
    "model": obj,
    "models": obj,
    "obj": obj,
    "environments": environment,
    "env": environment,
    "flavors": flavor,
    "fl": flavor,
    "s3": s3,
    "MLflow": mlflow,
    "mlflows": mlflow,
    "MLflows": mlflow
}
