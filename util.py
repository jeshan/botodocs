import os
from os import truncate, makedirs

import pythonic


def create_new_file(path):
    makedirs(path[: path.rindex('/')], exist_ok=True)
    try:
        truncate(path, 0)
    except FileExistsError as e:
        pass
    except FileNotFoundError as e:
        os.mknod(path)
    except Exception as e:
        raise e


def get_botostubs_message():
    return '> To get type hints mentioned above, install [botostubs](https://github.com/jeshan/botostubs): `pip install botostubs` and import it\n'


def get_link_to_client_function(name, service_path):
    return f'[{name}]({service_path}/client/operations/{name})'


def write_lines(path, lines):
    [write_to_file(path, line + '\n') for line in lines]


def write_to_file(path, contents):
    makedirs(path[: path.rindex("/")], exist_ok=True)
    with open(path, 'a') as f:
        f.write(contents)


def get_service_name(service_model):
    return service_model.metadata.get('serviceAbbreviation', service_model.metadata['serviceFullName'])


def get_shape_string_link(shape, shapes_path):
    if not shape:
        return ''
    if shape.type_name in primitive_map:
        return primitive_map[shape.type_name]
    return f'[{shape.name}]({shapes_path}#' + shape.name + ')' if shape else ''


primitive_map = {
    'string': 'str',
    'integer': 'int',
    'boolean': 'bool',
    'timestamp': 'datetime',
    'Float': 'float',
    'float': 'float',
    'long': 'int',
    'double': 'float',
    #'structure': 'dict',
}


def get_enum_message(param_value):
    if hasattr(param_value, 'enum') and param_value.enum:
        return f'\n_This is an enum, accepting values: `{"`, `".join(param_value.enum)}`_\n\n'
    return ''


def get_doc_str(shape, shapes_path):
    return get_doc_str_members(shape, shapes_path, shape.members if shape else {})


def get_doc_str_members(shape, shapes_path, members):
    docstr = ''
    if not shape or not hasattr(shape, 'members') or not shape.members.items():
        return docstr
    for param_key, param_value in sorted(members.items(), reverse=True):
        doc = param_value.documentation
        required_str = 'required type ' if param_key in shape.required_members else 'type '
        enum = get_enum_message(param_value)
        shape_link = get_shape_string_link(param_value, shapes_path)
        docstr = f"""**{param_key}** ({required_str}{shape_link}): \n> {doc}\n\n{enum}<br/>{docstr}"""
    return docstr


def get_returns_string(output_shape, shapes_path):
    string_link = get_shape_string_link(output_shape, shapes_path)
    return f"""## Returns
{f'_This return value is specified in greater detail in {string_link}._' if string_link else 'None'}
{output_shape.documentation + '' if output_shape else ''}
{'It has:' if output_shape else ''}

{get_doc_str(output_shape, shapes_path)}
"""


def get_accepts_string(input_shape, shapes_path):
    return get_accepts_string_members(input_shape, input_shape.members if input_shape else {}, shapes_path)


def get_accepts_string_members(input_shape, members, shapes_path):
    return f"""## Accepts
_The below arguments are specified in greater detail in {get_shape_string_link(input_shape, shapes_path)}._

{get_doc_str_members(input_shape, shapes_path, members)}
"""


def get_operation_documentation(operation_model, service_model):
    operation_name = operation_model.name
    service_name = service_model.service_name
    return (
        operation_model.documentation
        + f'\n\n>See also: [AWS API Documentation for {service_name}.{operation_name}](https://docs.aws.amazon.com/goto/WebAPI/{service_name}-{service_model.api_version}/{operation_name})'
        + '\n'
    )


def get_accepts_redirect_link(client_name, fn_name, service_path):
    return f"""_See {client_name}_client.[{fn_name}]({service_path}/client/operations/{fn_name}#Accepts) for parameters that you can pass in_
"""


def get_resource_path_for(resource_name, resource_path):
    is_sub_res = is_sub_resource(resource_path)
    if is_sub_res:
        new_resource_path = f'{resource_path[:resource_path.rindex("/")]}/{resource_name}'
    else:
        new_resource_path = f'{resource_path}/sub-resources/{resource_name}'
    return new_resource_path


def is_sub_resource(resource_path):
    return 'sub-resources' in resource_path


def get_variable_name_for(name):
    variable_name = pythonic.xform_name(name)
    if '_' in variable_name:
        variable_name = variable_name[variable_name.rindex('_') + 1 :]
    return variable_name
