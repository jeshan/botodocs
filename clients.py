from typing import List, Union, Dict

from botocore.model import ServiceModel, OperationModel, StringShape, ListShape, Shape, StructureShape, MapShape

import pythonic
from util import (
    create_new_file,
    get_botostubs_message,
    write_lines,
    get_service_name,
    get_shape_string_link,
    primitive_map,
    get_enum_message,
    get_returns_string,
    get_accepts_string,
    get_operation_documentation,
)

shape_union = Union[None, StringShape, ListShape, Shape, StructureShape, MapShape]
sidebar_path = 'docs/_sidebar.md'
services_path = 'docs/services.md'


def create_client_index(path, client_name, service_name, class_name):
    create_new_file(path)
    return [
        f'# {service_name} client',
        f'A low-level client representing {service_name}.',
        'There are 2 main ways of creating clients; with a default `boto3.Session` or with one that you define:',
        f"""```python
import boto3

client = boto3.client('{client_name}')  # type: botostubs.{class_name}
```
""",
        'or ...',
        f"""```python
from boto3 import Session

session = Session(profile_name='your-aws-cli-profile')
client = session.client('{client_name}')  # type: botostubs.{class_name}
```""",
        get_botostubs_message(),
        '# Operations',
        'These are the available operations:',
    ]


def handle_client(client, client_name, class_name, service_path, sidebar_lines, shapes_path):
    print('handling client', client_name)
    service_model: ServiceModel = client._service_model
    service_name = get_service_name(service_model)
    service_id = service_model.service_id

    client_path = f'{service_path}/client'
    sidebar_lines.append(f'        - [{service_id} client]({client_path})')
    docs_client_path = f'docs/{client_path}.md'
    client_list_items = create_client_index(docs_client_path, client_name, service_name, class_name)
    for name in service_model.operation_names:
        handle_client_operation(
            class_name, client_list_items, client_name, client_path, name, service_model, shapes_path
        )
    write_lines(docs_client_path, client_list_items)
    handle_shapes(service_model, class_name, shapes_path)


def handle_client_operation(class_name, client_list_items, client_name, client_path, name, service_model, shapes_path):
    fn_name = pythonic.xform_name(name)
    method_path = f'{client_path}/operations/{fn_name}.md'
    list_item, signature, documentation, headline = get_method_page(
        client_name, class_name, service_model, name, method_path, shapes_path
    )
    docs_method_path = f'docs/{method_path}'
    create_new_file(docs_method_path)
    write_lines(docs_method_path, [headline, documentation, signature])
    client_list_items.append(list_item)


def get_example_client_snippet(client_name, service, fn_name, parameters, required_members, output_shape):
    result_type_hint = f'  # type: botostubs.{service}.{output_shape.name}' if output_shape else ''

    param_str = get_parameter_declaration_with(parameters, required_members)
    return f"""## Example snippet
```python
import boto3

client = boto3.client('{client_name}')  # type: botostubs.{service}
result = client.{fn_name}({param_str}){result_type_hint}
```
{get_botostubs_message()}"""


def get_shape_doc(shapes_path, shape: shape_union):
    docstr = f'## {shape.name}\n'
    docstr += f'> {shape.documentation}\n\n'
    if hasattr(shape, 'members'):
        members = sorted(shape.members.items())
    elif hasattr(shape, 'member'):
        members = [(shape.member.name, shape.member)]
    elif isinstance(shape, MapShape):
        members = [('Key', shape.key), ('Value', shape.value)]
    else:
        members = []
    word = 'containing:\n\n' if len(members) > 1 else 'of: '
    docstr += f'A {get_familiar_type_name(shape)} {word}'
    for param_key, param_value in members:
        documentation = param_value.documentation
        doc = f': \n\n > {documentation}\n\n' if documentation else '\n'

        required_str = 'required ' if param_key in shape.required_members else ''
        name = param_key
        if param_key != param_value.name:
            type_of_x = get_type_of_x_message(shapes_path, param_value, required_str)
            docstr += f"""<b>{name}</b> ({type_of_x})"""
        elif param_value.name.lower() in primitive_map:
            docstr += f"""<b>{name}</b>"""
        else:
            docstr += f"""<b>[{name}]({shapes_path}#{name})</b>"""
        docstr += doc + '\n'
        docstr += get_enum_message(param_value)
    return docstr


def get_signature_string(
    client_name, class_name, input_shape, output_shape, fn_name, param_str, shapes_path, append_return_type
):
    required_members = input_shape.required_members if input_shape else []
    parameters = input_shape.members if input_shape else {}
    signature_header = f"""## Signature
**{fn_name}**({param_str}){append_return_type}
"""
    return f"""{signature_header}
{get_example_client_snippet(client_name, class_name, fn_name, parameters, required_members, output_shape)}

{get_accepts_string(input_shape, shapes_path)}

{get_returns_string(output_shape, shapes_path)}"""


def get_method_page(client_name, class_name, service_model, operation_name, method_path, shapes_path):
    pythonic_op_name = pythonic.xform_name(operation_name)
    operation_model: OperationModel = service_model.operation_model(operation_name)
    input_shape: shape_union = operation_model.input_shape
    output_shape: shape_union = operation_model.output_shape

    param_str = get_param_str(input_shape, shapes_path)
    append_return_type = ' -> ' + get_shape_string_link(output_shape, shapes_path) if output_shape else ''

    signature = get_signature_string(
        client_name, class_name, input_shape, output_shape, pythonic_op_name, param_str, shapes_path, append_return_type
    )
    headline = f'# {pythonic_op_name} operation'
    documentation = get_operation_documentation(operation_model, service_model)
    list_item = f'-  **[{pythonic_op_name}]({method_path})**({param_str}){append_return_type}'
    return list_item, signature, documentation, headline


def handle_shapes(service_model: ServiceModel, class_name, shapes_path):
    top_level_shapes = [(service_model.shape_for(name), class_name) for name in service_model.shape_names]
    if not top_level_shapes:
        return
    docs_shapes_path = f'docs/{shapes_path}'
    create_new_file(docs_shapes_path)
    service_name = get_service_name(service_model)
    all_shapes = find_all_shapes(top_level_shapes)
    shape_docs = [get_shape_doc(shapes_path, shape) for shape in all_shapes]
    write_lines(docs_shapes_path, [f'# {service_name} data types'] + shape_docs)


def get_parameter_declaration_with(params: Dict[str, shape_union], required_members: List[str]):
    return ', '.join(map(lambda x: param_to_string(x, params[x]), filter(lambda x: x in required_members, params)))


def get_familiar_type_name(shape):
    name = shape.type_name
    if name == 'structure':
        return 'dictionary'
    if name == 'list':
        if shape.name.endswith('Set'):
            name = 'set'
    return name


def get_type_of_x_message(shapes_path, param_value, required_str):
    if param_value.type_name in primitive_map:
        return param_value.type_name
    # if param_value.name in primitive_map:
    #   return primitive_map[param_value.name]
    return f'{required_str}[{param_value.name}]({shapes_path}#{param_value.name}) {get_familiar_type_name(param_value)}'


def get_param_name_with_type_hint(shape, name, param, shapes_path):
    if param.type_name == 'list':
        type_hint = f'[{param.name}]({shapes_path}#{param.name})'
    else:
        type_hint = primitive_map.get(param.type_name, param.type_name)
    if name not in shape.required_members:
        type_hint = f'Optional[{type_hint}]'
    item = f'{name}:*{type_hint}*'
    return item


def get_param_name(shape, name, param):
    if param.type_name == 'list':
        item = param.name
    else:
        item = primitive_map.get(param.type_name, param.type_name)
    if name not in shape.required_members:
        item = f'{item}=None'

    return item


def get_param_str(input_shape, shapes_path):
    parameters = input_shape.members if input_shape else {}
    return get_param_str_params(input_shape, shapes_path, parameters)


def get_param_str_params(input_shape, shapes_path, parameters):
    param_list = []
    for name, param in parameters.items():
        item = get_param_name_with_type_hint(input_shape, name, param, shapes_path)
        if name in input_shape.required_members:
            param_list.insert(0, item)
        else:
            param_list.append(item)
    return ', '.join(param_list)


def find_all_shapes(shapes):
    result = list(_find_all_shapes(list(map(lambda x: x[0], shapes)), []))
    unique_shapes = ordered_set(result)
    return sorted(unique_shapes, key=lambda x: x.name)


def param_to_string(name, shape):
    def member_to_string(key):
        result = f"'{key}': "
        member_shape = shape.members[key]
        if member_shape.type_name == 'string':
            result += "'...'"
        elif member_shape.type_name == 'boolean':
            result += "True"
        elif member_shape.type_name in ['integer', 'float']:
            result += '0'
        return result

    result = name
    if shape.type_name == 'list':
        if isinstance(shape.member, StringShape):
            result += "=['...']"
        else:
            result += '=[{}]'
    elif shape.type_name == 'string':
        result += "='...'"
    elif shape.type_name == 'boolean':
        result += "=True"
    elif shape.type_name == 'structure':
        result += '={'

        if shape.required_members:
            result += ', '.join(map(member_to_string, shape.required_members))
        result += '}'
    return result


def _find_all_shapes(shapes, parent_shapes):
    result = []
    for shape in shapes:
        if shape.type_name in primitive_map:
            continue
        if shape.type_name == 'blob':
            # nothing interesting with a blob
            continue
        members = []
        if hasattr(shape, 'member'):
            members = [shape.member]
        elif hasattr(shape, 'members'):
            members = list(shape.members.values())
        elif isinstance(shape, MapShape):
            members = [shape.key, shape.value]
        else:
            assert False
        # to prevent infinite recursion which will happen if shape references itself down the stack
        new_members = list(filter(lambda x: not contains_shapes(members, parent_shapes), members))
        result.append(shape)
        result.extend(_find_all_shapes(new_members, parent_shapes + [shape]))
    return result


def ordered_set(inlist):
    out_list = []
    for val in inlist:
        if not contains_shapes(out_list, [val]):
            out_list.append(val)
    return out_list


def contains_shapes(shape_list, params):
    for item in shape_list:
        for param in params:
            if item.name == param.name:
                return True
