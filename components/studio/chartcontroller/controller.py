import subprocess
import json
import yaml
import shlex

import os
import uuid
import flatten_json
import yaml

def deploy(options):
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, 'app/chartcontroller/config/config')
    chart = 'charts/'+options['chart']

    # if 'DEBUG' in os.environ and os.environ['DEBUG'] == 'true':
    #     if not 'chart' in options:
    #         print('Chart option not specified.')
    #         return json.dumps({'status':'failed', 'reason':'Option chart not set.'})
    #     chart = 'charts/scaleout/'+options['chart']
    # else:
    #     refresh_charts(self.branch)
    #     fname = self.branch.replace('/', '-')
    #     chart = 'charts-{}/scaleout/{}'.format(fname, options['chart'])

    if not 'release' in options:
        print('Release option not specified.')
        return json.dumps({'status':'failed', 'reason':'Option release not set.'})


    unique_filename = 'chartcontroller/values/{}.yaml'.format(str(uuid.uuid4()))
    f = open(unique_filename,'w')
    f.write(yaml.dump(options))
    f.close()
    print(yaml.dump(options))


    args = ['helm', 'upgrade', '--install', '--kubeconfig', kubeconfig, '-n', options['namespace'], options['release'], chart, '-f', unique_filename]
    print("PROCESSING INPUT TO CONTROLLER")

    

    status = subprocess.run(args)
    print(status, flush=True)
    return status

def delete(options):
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, 'app/chartcontroller/config/config')
    # print(type(options))
    # print(options)
    # args = 'helm --kubeconfig '+str(kubeconfig)+' delete {release}'.format(release=options['release']) #.split(' ')
    args = ['helm', '--kubeconfig', str(kubeconfig), '-n', options['namespace'], 'delete', options['release']]
    status = subprocess.run(args)
    print("DELETE STATUS FROM CONTROLLER")
    print(status, flush=True)
    return status
    # return json.dumps({'helm': {'command': args, 'cwd': str(self.cwd), 'status': str(status)}})