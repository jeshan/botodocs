from typing import List

import boto3
from boto3.resources.base import ServiceResource
from boto3.resources.model import Parameter
from botocore.model import ServiceModel

import pythonic
from clients import get_parameter_declaration_with, get_param_str, get_param_str_params
from resource_collections import handle_collections
from util import (
    write_lines,
    create_new_file,
    get_botostubs_message,
    get_returns_string,
    get_operation_documentation,
    get_accepts_string_members,
    get_resource_path_for,
    is_sub_resource,
    get_variable_name_for,
)

# noinspection PyUnresolvedReferences
import botostubs


from waiters import handle_sub_resource_waiters


def handle_sub_resource(
    resource_name,
    sub_resource,
    sidebar_lines,
    resource_path,
    resource_list_items,
    class_name,
    service_model,
    shapes_path,
    service_path,
):
    sub_resource_name = sub_resource.name
    sub_resource_path = f'{resource_path}/sub-resources/{sub_resource_name}'
    docs_sub_resource_path = f'docs/{sub_resource_path}.md'
    list_item = f'-  **[{sub_resource_name}]({sub_resource_path})**'
    resource_list_items.append(list_item)
    sidebar_lines.append(f'          - [{sub_resource_name} sub-resource]({sub_resource_path})')

    param_str = get_sub_resource_param_str(sub_resource)
    sub_resource_shape_name = sub_resource.resource.model.shape
    sub_resource_list_items = create_sub_resource_index(
        docs_sub_resource_path,
        resource_name,
        class_name,
        sub_resource_name,
        param_str,
        sub_resource_shape_name,
        shapes_path,
    )
    actions = sub_resource.resource.model.actions
    handle_resource_actions(
        resource_name, class_name, sub_resource_list_items, sub_resource_path, service_model, shapes_path, actions
    )
    collections = sub_resource.resource.model.collections
    handle_collections(
        collections, sub_resource_list_items, sub_resource_path, class_name, service_model, resource_name, service_path
    )
    handle_sub_resource_waiters(sub_resource, sub_resource_list_items, service_path)

    write_lines(docs_sub_resource_path, sub_resource_list_items)


def get_sub_resource_param_str(sub_resource):
    params = []
    for identifier in sub_resource.resource.identifiers:
        params.append(pythonic.xform_name(identifier.target) + "='...'")
    param_str = ', '.join(params)
    return param_str


def handle_resource_action(
    client_name, class_name, action, method_path, fn_name, service_model: ServiceModel, shapes_path, resource_path
):
    operation_model = service_model.operation_model(action.request.operation)
    input_shape = operation_model.input_shape

    has_output_shape = action.resource and action.resource.model.shape in service_model.shape_names
    output_shape = service_model.shape_for(action.resource.model.shape) if has_output_shape else None

    output_name = action.resource.model.name if action.resource else None
    if output_name:
        new_path = get_resource_path_for(output_name, resource_path)
        append_return_type = ' -> ' + f'[{output_name}]({new_path})'
    else:
        append_return_type = ''

    sub_res_var_name = None
    is_sub_res = is_sub_resource(resource_path)
    parameters = input_shape.members if input_shape else {}
    if is_sub_res:
        sub_res_name = resource_path[resource_path.rindex('/') + 1 :]
        sub_res_var_name = get_variable_name_for(sub_res_name)
        request_params = list(map(lambda x: x.target, action.request.params))
        if input_shape:
            include_params = {name: value for name, value in input_shape.members.items() if name not in request_params}
        else:
            include_params = {}
        param_str = get_param_str_params(input_shape, shapes_path, include_params)
    else:
        if input_shape:
            include_params = {
                name: value for name, value in input_shape.members.items() if name in input_shape.required_members
            }
        else:
            include_params = {}
        param_str = get_param_str(input_shape, shapes_path)
    signature = get_signature_string(
        client_name,
        class_name,
        input_shape,
        output_shape,
        fn_name,
        param_str,
        shapes_path,
        append_return_type,
        sub_res_var_name,
        parameters,
        include_params,
    )
    documentation = get_operation_documentation(operation_model, service_model)

    headline = f'# {fn_name} action'
    list_item = f'-  **[{fn_name}]({method_path})**({param_str}){append_return_type}'
    return list_item, signature, documentation, headline


def get_example_resource_snippet(client_name, service, fn_name, parameters, required_members, output_shape):
    result_type_hint = f'  # type: botostubs.{service}.{output_shape.name}' if output_shape else ''

    param_str = get_parameter_declaration_with(parameters, required_members)
    return f"""## Example snippet
```python
import boto3

resource = boto3.resource('{client_name}')  # type: botostubs.{service}.{service}Resource
result = resource.{fn_name}({param_str}){result_type_hint}
```
{get_botostubs_message()}"""


def get_example_sub_resource_snippet(variable_name, service, fn_name, parameters, required_members, output_shape):
    result_type_hint = f'  # type: botostubs.{service}.{output_shape.name}' if output_shape else ''

    param_str = get_parameter_declaration_with(parameters, required_members)
    return f"""## Example snippet
```python
result = {variable_name}.{fn_name}({param_str}){result_type_hint}
```
{get_botostubs_message()}"""


def get_signature_string(
    client_name,
    class_name,
    input_shape,
    output_shape,
    fn_name,
    param_str,
    shapes_path,
    append_return_type,
    sub_res_var_name,
    parameters,
    include_params,
):
    signature_header = f"""## Signature
**{fn_name}**({param_str}){append_return_type}
"""
    if sub_res_var_name:
        snippet = get_example_sub_resource_snippet(
            sub_res_var_name, class_name, fn_name, parameters, include_params.keys(), output_shape
        )
    else:
        snippet = get_example_resource_snippet(
            client_name, class_name, fn_name, parameters, include_params.keys(), output_shape
        )
    return f"""{signature_header}
{snippet}

{get_accepts_string_members(input_shape, include_params, shapes_path)}

{get_returns_string(output_shape, shapes_path)}"""


def handle_resource_actions(client_name, class_name, list_items, resource_path, service_model, shapes_path, actions):
    if actions:
        list_items.extend(['# Actions', 'These are the available actions:'])
    for action in actions:
        fn_name = action.name
        method_path = f'{resource_path}/operations/{fn_name}.md'
        list_item, signature, documentation, headline = handle_resource_action(
            client_name, class_name, action, method_path, fn_name, service_model, shapes_path, resource_path
        )
        docs_method_path = f'docs/{method_path}'
        create_new_file(docs_method_path)
        write_lines(docs_method_path, [headline, documentation, signature])
        list_items.append(list_item)
    if actions:
        list_items.append('')  # newline


def create_resource_index(path, resource_name, service_name, class_name):
    create_new_file(path)
    return [
        f'# {service_name} resource',
        f'A resource representing {service_name}:\n',
        'You create such a resource as follows:',
        f"""```python
import boto3

resource = boto3.resource('{resource_name}')  # type: botostubs.{class_name}.{class_name}Resource
```
""",
        get_botostubs_message(),
    ]


def get_resource_equivalence_message(name, shape_name, path):
    if not shape_name:
        return ''
    suffix = f'[{shape_name}]({path}#{shape_name})_\n'
    if name != shape_name:
        return f'_{name} has its attributes detailed in {suffix}'
    return f'_{suffix} specs'


def create_sub_resource_index(
    path, resource_name, class_name, sub_resource_name, param_str, sub_resource_shape_name, shapes_path
):
    create_new_file(path)
    sub_resource_variable = pythonic.xform_name(sub_resource_name)
    if '_' in sub_resource_variable:
        sub_resource_variable = sub_resource_variable[sub_resource_variable.rindex('_') + 1 :]
    resource_hint = f"botostubs.{class_name}.{class_name}Resource"
    sub_resource_title = f'{class_name}.{sub_resource_name}'
    return [
        f'# {sub_resource_title} sub-resource',
        f'A sub-resource representing `{sub_resource_title}`:\n',
        'You create such a resource as follows:',
        f"""```python
import boto3

resource = boto3.resource('{resource_name}')  # type: {resource_hint}
{sub_resource_variable} = resource.{sub_resource_name}({param_str})  # type: {resource_hint}.{sub_resource_name}
```
""",
        get_resource_equivalence_message(sub_resource_name, sub_resource_shape_name, shapes_path),
        get_botostubs_message(),
    ]


def get_collection_parameter_declaration(parameters: List[Parameter]):
    return ', '.join(map(lambda x: x.value, parameters))


def handle_resources(client, resource_name, class_name, service_name, service_path, sidebar_lines):
    try:
        resource: ServiceResource = boto3.resource(resource_name)
    except boto3.exceptions.ResourceNotExistsError:
        return
    service_model: ServiceModel = client._service_model
    service_id = service_model.service_id
    shapes_path = f'{service_path}/data-types.md'
    resource_path = f'{service_path}/resource'
    sidebar_lines.append(f'        - [{service_id} resource]({resource_path})')

    docs_resource_path = f'docs/{resource_path}.md'
    resource_list_items = create_resource_index(docs_resource_path, resource_name, service_name, class_name)
    resource_model = resource.meta.resource_model
    actions = resource_model.actions
    handle_resource_actions(
        resource_name, class_name, resource_list_items, resource_path, service_model, shapes_path, actions
    )

    collections = resource_model.collections
    handle_collections(
        collections, resource_list_items, resource_path, class_name, service_model, resource_name, service_path
    )
    sub_resources = resource_model.subresources
    if sub_resources:
        resource_list_items.append('\n')
        resource_list_items.append('# Sub-resources')
        resource_list_items.append('These are the available sub-resources:')
    for sub_resource in sub_resources:
        handle_sub_resource(
            resource_name,
            sub_resource,
            sidebar_lines,
            resource_path,
            resource_list_items,
            class_name,
            service_model,
            shapes_path,
            service_path,
        )

    write_lines(docs_resource_path, resource_list_items)
