import botocore

import pythonic
from util import (
    create_new_file,
    get_botostubs_message,
    get_link_to_client_function,
    write_lines,
    get_accepts_redirect_link,
)


def create_paginator_index(path, client_name, service_name, example_paginator_name):
    create_new_file(path)
    return [
        f'# {service_name} paginators',
        f"""You get a paginator by calling `get_paginator` on a certain client:
```python
import boto3

client = boto3.client('{client_name}')
paginator = client.get_paginator('{pythonic.xform_name(example_paginator_name)}')  # type: botostubs.{service_name}.{example_paginator_name}Paginator
```
""",
        get_botostubs_message(),
        'The available client paginators are:',
    ]


def get_example_paginator_snippet(paginator, name, client_name, service, fn_name, service_path):

    return f"""```python
import boto3

client = boto3.client('{client_name}')
paginator = client.get_paginator('{fn_name}')  # type: botostubs.{service}.{name}Paginator
response_iterator = paginator.paginate(
    PaginationConfig={{'MaxItems': 123, 'PageSize': 123, 'StartingToken': previous_response.get('{paginator["output_token"]}')}}, OtherParams=...
)
```
{get_botostubs_message()}

### Accepts
{get_accepts_redirect_link(client_name, fn_name, service_path)}
### Returns
_See {client_name}_client.[{fn_name}]({service_path}/client/operations/{fn_name}#Returns) for the response contents._
"""


def get_paginator_page(name, pythonic_name, client_name, class_name, paginator, paginator_path, service_path):
    headline = f'# {pythonic_name} paginator'
    signature = f"""

{get_example_paginator_snippet(paginator, name, client_name, class_name, pythonic_name, service_path)}
"""
    documentation = f'Creates an iterator that will paginate through responses from {client_name}_client.{get_link_to_client_function(pythonic_name, service_path)}'
    list_item = f'- [{pythonic_name}]({paginator_path})'
    return list_item, signature, documentation, headline


def handle_paginators(client_name, class_name, service_name, service_path, sidebar_lines):
    try:
        model = botocore.session.get_session().get_paginator_model(client_name)
    except botocore.exceptions.UnknownServiceError:
        return

    paginator_config = model._paginator_config
    if not paginator_config:
        return
    paginator_names = list(paginator_config.keys())
    if not paginator_names:
        return
    paginators_path = f'{service_path}/paginators'
    sidebar_lines.append(f'          - [Paginators]({paginators_path})')
    docs_paginators_path = f'docs/{paginators_path}.md'
    example_paginator_name = paginator_names[0]
    paginator_list_items = create_paginator_index(
        docs_paginators_path, client_name, service_name, example_paginator_name
    )
    for name, paginator in sorted(paginator_config.items()):
        pythonic_name = pythonic.xform_name(name)
        paginator_path = f'{paginators_path}/{pythonic_name}'
        docs_pagination_path = f'docs/{paginator_path}.md'
        create_new_file(docs_pagination_path)
        list_item, signature, documentation, headline = get_paginator_page(
            name, pythonic_name, client_name, class_name, paginator, paginator_path, service_path
        )
        create_new_file(docs_pagination_path)
        write_lines(docs_pagination_path, [headline, documentation, signature])
        paginator_list_items.append(list_item)

    write_lines(docs_paginators_path, paginator_list_items)
