import sys

import boto3
from botocore.model import ServiceModel

from clients import sidebar_path, handle_client, services_path

from paginators import handle_paginators
from resources import handle_resources
from util import create_new_file, write_lines, get_service_name, write_to_file
from waiters import handle_waiters


def create_sidebar():
    create_new_file(sidebar_path)
    return ["- [Overview](README.md)", "- [Services](services.md)"]


def create_services_page():
    create_new_file(services_path)
    return ['# List of supported services']


def create_readme():
    path = 'docs/README.md'
    create_new_file(path)
    write_to_file(
        path,
        f"""# Overview

Welcome to botodocs! This site serves as the unofficial boto3 reference for its features.

These include the boto3:
- clients
- resources
- sub-resources
- waiters
- paginators
- collections

_and all data types that they use_.

It has been designed for better usability than the official docs, namely by providing:
- make service pages less dense
- copy-pastable snippets covering the various boto3 features
- offline search

You're looking at the docs for boto3 version **{boto3.__version__}**. This site is automatically deployed every 3 days so you should see full feature coverage here.

Note that the official boto3 guides have been left out and you should consult the official website for that:

https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
""",
    )


def go():
    boto3.setup_default_session()
    clients = boto3.DEFAULT_SESSION.get_available_services()
    sidebar_lines = create_sidebar()
    services_lines = create_services_page()
    create_readme()
    for index, client_name in enumerate(clients):
        # if client_name not in ['ec2', 'accessanalyzer', 'glacier', 'ssm', 'wafv2', 'cloudformation']:
        #   continue
        client = boto3.client(client_name)
        class_name = type(client).__name__
        service_model: ServiceModel = client._service_model
        name_in_path = service_model.endpoint_prefix
        service_path = f'services/{name_in_path}'
        shapes_path = f'{service_path}/data-types.md'
        service_name = get_service_name(service_model)

        handle_service(client, service_path, service_model, sidebar_lines, services_lines)
        handle_client(client, client_name, class_name, service_path, sidebar_lines, shapes_path)

        handle_paginators(client_name, class_name, service_name, service_path, sidebar_lines)
        handle_waiters(client, client_name, class_name, service_name, service_path, sidebar_lines)
        handle_resources(client, client_name, class_name, service_name, service_path, sidebar_lines)
        sidebar_lines.append(f'        - [Data Types]({shapes_path})')
    write_lines(sidebar_path, sidebar_lines)
    write_lines(services_path, services_lines)


def handle_service(client, service_path, service_model, sidebar_lines, services_lines):
    service_name = get_service_name(service_model)
    service_documentation_html = client.meta._service_model.documentation
    sidebar_lines.append(f'    - [{service_name}]({service_path})')
    services_lines.append(f'  - [{service_name}]({service_path})')
    docs_service_path = f'docs/{service_path}.md'
    create_new_file(docs_service_path)
    write_lines(docs_service_path, [f'# {service_name}', service_documentation_html])


def serve_docs():
    from subprocess import run

    # that's for my own convenience :)
    run('/home/jeshan/.nvm/versions/node/v10.13.0/bin/docsify serve docs'.split(' '))


if __name__ == "__main__":
    go()
    if len(sys.argv) > 1 and sys.argv[1]:
        serve_docs()
