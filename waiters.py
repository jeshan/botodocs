from boto3.resources.model import Action, Waiter
from botocore.waiter import WaiterModel

import pythonic
from util import create_new_file, get_botostubs_message, get_link_to_client_function, write_lines, get_variable_name_for


def create_waiter_index(path, client_name, service_name, waiter_name):
    create_new_file(path)
    return [
        f'# {service_name} waiters',
        f"""You get a waiter by calling `get_waiter` on a certain client:
```python
import boto3

client = boto3.client('{client_name}')
waiter = client.get_waiter('{pythonic.xform_name(waiter_name)}')  # type: botostubs.{service_name}.{waiter_name}Waiter
```
""",
        get_botostubs_message(),
        'The available client waiters are:',
    ]


def get_example_waiter_snippet(name, pythonic_name, client_name, service, fn_name, service_path):
    return f"""```python
import boto3

client = boto3.client('{client_name}')
waiter = client.get_waiter('{pythonic_name}')  # type: botostubs.{service}.{name}Waiter
waiter.wait(
    WaiterConfig={{'Delay': 123, 'MaxAttempts': 123}}, OtherParams=...    
)
```
{get_botostubs_message()}

### Accepts
_See {client_name}_client.[{fn_name}]({service_path}/client/operations/{fn_name}#Accepts) for other parameters that you can pass in._

### Returns
None
"""


def get_waiter_page(name, fn_name, client_name, class_name, waiter_path, service_path):
    pythonic_name = pythonic.xform_name(name)
    headline = f'# {pythonic_name} waiter'
    signature = f"""

{get_example_waiter_snippet(name, pythonic_name, client_name, class_name, fn_name, service_path)}
"""
    documentation = f'Polls {client_name}_client.{get_link_to_client_function(fn_name, service_path)} every 15 seconds until a successful state is reached. An error is returned after 40 failed checks.'
    list_item = f'- [{pythonic_name}]({waiter_path})'
    return list_item, signature, documentation, headline


def handle_waiters(client, client_name, class_name, service_name, service_path, sidebar_lines):
    waiter_config = client._get_waiter_config()
    waiter_model = WaiterModel(waiter_config) if 'waiters' in waiter_config else None

    if not waiter_model:
        return

    waiters_path = f'{service_path}/waiters'
    sidebar_lines.append(f'          - [Waiters]({waiters_path})')
    docs_waiters_path = f'docs/{waiters_path}.md'
    waiter_names = waiter_model.waiter_names
    example_waiter_name = waiter_names[0]
    waiter_list_items = create_waiter_index(docs_waiters_path, client_name, service_name, example_waiter_name)

    for name in waiter_names:
        handle_waiter(class_name, client_name, name, service_path, waiter_list_items, waiter_model, waiters_path)

    write_lines(docs_waiters_path, waiter_list_items)


def handle_waiter(class_name, client_name, name, service_path, waiter_list_items, waiter_model, waiters_path):
    waiter = waiter_model.get_waiter(name)
    pythonic_name = pythonic.xform_name(waiter.operation)
    waiter_path = f'{waiters_path}/{pythonic.xform_name(name)}'
    docs_waiter_path = f'docs/{waiter_path}.md'
    create_new_file(docs_waiter_path)
    list_item, signature, documentation, headline = get_waiter_page(
        name, pythonic_name, client_name, class_name, waiter_path, service_path
    )
    create_new_file(docs_waiter_path)
    write_lines(docs_waiter_path, [headline, documentation, signature])
    waiter_list_items.append(list_item)


def handle_sub_resource_waiters(resource: Action, resource_list_items, service_path):
    waiters = resource.resource.model.waiters
    if waiters:
        resource_list_items.extend(['# Waiters', 'The following waiters are available:'])
    waiters_path = f'{service_path}/waiters'
    waiter: Waiter
    for waiter in waiters:
        name = pythonic.xform_name(waiter.waiter_name)
        variable_name = get_variable_name_for(resource.name)
        resource_list_items.append(f'## {waiter.name}')
        resource_list_items.append(
            f"""```python
{variable_name}.{waiter.name}(...)
```
"""
        )
        resource_list_items.append(
            f'> Note that this waiter delegates to the client [{name}]({waiters_path}/{name}) waiter'
        )
