import logging

import requests as r
from django.conf import settings


def pod_up(app_name):
    num_pods_up = 0
    num_pods_count = 0
    try:
        query_up = 'sum(up{app="'+app_name+'"})'
        query_count = 'count(up{app="'+app_name+'"})'
        print(query_up)
        print(query_count)
        print(f'{settings.PROMETHEUS_SVC}/api/v1/query')
        response = r.get(
            f'{settings.PROMETHEUS_SVC}/api/v1/query',
            params={'query': query_up},
        )
        num_pods_up = 0
        num_pods_count = 0
        if response:
            print(response.text)
            result_up_json = response.json()
            result_up = result_up_json['data']['result']

        if response := r.get(
            f'{settings.PROMETHEUS_SVC}/api/v1/query',
            params={'query': query_count},
        ):
            result_count_json = response.json()
            result_count = result_count_json['data']['result']
        num_pods_up = result_up[0]['value'][1]
        num_pods_count = result_count[0]['value'][1]
    except:
        logging.warning(f'Failed to fetch status of app {app_name}')
    return num_pods_up, num_pods_count


def get_count_over_time(name, app_name, path, status_code, time_span):
    total_count = 0
    # Strip path of potential /
    path = path.replace('/', '')
    try:
        query = (
            f'sum(max_over_time({name}'
            + '{app="'
            + app_name
            + '", path="/'
            + path
            + '/", status_code="'
            + status_code
            + '"}['
            + time_span
            + ']))'
        )
        if response := r.get(
            f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
        ):
            total_count = response.json()['data']['result'][0]['value'][1]
    except:
        print(f'Failed to get total count for: {app_name}, {path}, {status_code}.')

    return total_count


def get_total_labs_cpu_usage_60s(project_slug):
    query = 'sum(sum (rate (container_cpu_usage_seconds_total{image!=""}[60s])) by (pod) * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'", label_app="lab"})'
    print(query)
    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        cpu_usage = result[0]['value'][1]
        return "{:.1f}".format(float(cpu_usage))
    return 0


def get_total_cpu_usage_60s_ts(project_slug, resource_type):
    query = '''(sum (sum ( irate (container_cpu_usage_seconds_total{image!=""}[60s] ) ) by (pod) * on(pod) group_left kube_pod_labels{label_type="''' + \
        resource_type+'",label_project="'+project_slug+'"})) [30m:30s]'
    print(query)
    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        return result[0]['values']
    return 0


def get_total_labs_memory_usage_60s(project_slug):
    query = 'sum(sum (rate (container_memory_usage_bytes{image!=""}[60s])) by (pod) * on(pod) group_left kube_pod_labels{label_project="' + \
        project_slug+'", label_app="lab"})'
    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        memory_usage = result[0]['value'][1]
        return "{:.3f}".format(float(memory_usage)/1e9*0.931323)
    return 0


def get_labs_memory_requests(project_slug):
    query = 'sum(kube_pod_container_resource_requests_memory_bytes * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'"})'
    # query = 'kube_pod_container_resource_requests_cpu_cores'

    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        memory = result[0]['value'][1]
        return "{:.2f}".format(float(memory)/1e9*0.931323)
    return 0


def get_labs_cpu_requests(project_slug):
    query = 'sum(kube_pod_container_resource_requests_cpu_cores * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'"})'

    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        return result[0]['value'][1]
    return 0


def get_resource(project_slug, resource_type, q_type, mem_or_cpu, app_name=[]):
    query = (
        f'sum(kube_pod_container_resource_{q_type}_{mem_or_cpu}'
        + ' * on(pod) group_left kube_pod_labels{label_project="'
        + project_slug
        + '", label_type="'
        + resource_type
        + '"'
    )
    query += f', label_app="{app_name}' + '"})' if app_name else '})'
    response = r.get(
        f'{settings.PROMETHEUS_SVC}/api/v1/query', params={'query': query}
    )
    if result := response.json()['data']['result']:
        return result[0]['value'][1]
    return '0.0'


def get_all():
    query = 'kube_pod_container_resource_limits_memory_bytes * on(pod) group_left kube_pod_labels{label_type="lab", label_project="stochss-dev-tiz"}'
    response = r.get(settings.PROMETHEUS_SVC +
                     '/api/v1/query', params={'query': query})
    result = response.json()['data']['result']
    print(result)
