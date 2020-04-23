from boto3.resources.model import Collection, Action
from botocore.model import OperationModel

import pythonic
from clients import get_parameter_declaration_with
from util import create_new_file, get_accepts_redirect_link, get_botostubs_message, get_resource_path_for, write_lines


def create_collection_page(
    path, collection_name, resource_name, class_name, parameter_str, client_name, service_path, op_name, resource_path
):
    create_new_file(path)

    def all():
        return f'Creates an iterable of all {resource_name} resources in the collection', ''

    def filter():
        return f'{all()[0]} filtered by kwargs passed to the method', parameter_str

    def limit():
        return (
            f'Creates an iterable up to a specified number of {resource_name} resources in the collection',
            'count=123',
        )

    def page_size():
        return (
            f'Creates an iterable of all {resource_name} resources in the collection, but limits the number of items returned by each service call by the specified number',
            'count=123',
        )

    new_resource_path = get_resource_path_for(resource_name, resource_path)
    result = [
        f'# {collection_name} collection',
        f'A collection of [{resource_name}]({new_resource_path}) resources:\n',
        '# Actions',
    ]
    for fn in [all, filter, limit, page_size]:
        result.append(f'## {fn.__name__}')
        doc, param_str = fn()
        result.append(doc)
        item_name = pythonic.xform_name(resource_name)
        result.append(
            f"""```python
{item_name}: botostubs.{class_name}.{class_name}Resource.{resource_name}
for {item_name} in resource.{collection_name}.{fn.__name__}({param_str}):
    pass # TODO: add your code here
```
"""
        )
        if fn == filter:
            pythonic_op_name = pythonic.xform_name(op_name)
            result.append(
                f"""#### Accepts
{get_accepts_redirect_link(client_name, pythonic_op_name, service_path)}
"""
            )
    result.append(get_botostubs_message())
    return result


def handle_collections(
    collections, resource_list_items, resource_path, class_name, service_model, client_name, service_path
):
    if collections:
        resource_list_items.extend(['# Collections', 'These are the available collections:'])
    collection: Collection
    for collection in collections:
        name = collection.name
        collection_path = f'{resource_path}/collections/{name}'
        docs_collection_path = f'docs/{collection_path}.md'
        list_item = f'-  **[{name}]({collection_path})**'
        resource_list_items.append(list_item)
        resource_name = collection.resource.model.name

        op_name = collection.request.operation
        param_str = get_param_str_from_operation(op_name, service_model)

        collection_list_items = create_collection_page(
            docs_collection_path,
            name,
            resource_name,
            class_name,
            param_str,
            client_name,
            service_path,
            op_name,
            resource_path,
        )

        handle_batch_actions(client_name, collection, collection_list_items, service_path)
        write_lines(docs_collection_path, collection_list_items)
    if collections:
        resource_list_items.append('')  # newline


def handle_batch_actions(client_name, collection, collection_list_items, service_path):
    if collection.batch_actions:
        collection_list_items.append('# Batch actions')
    action: Action
    for action in collection.batch_actions:
        op_name = action.request.operation
        collection_list_items.append(f'## {action.name}')
        collection_list_items.append(
            f'> {get_accepts_redirect_link(client_name, pythonic.xform_name(op_name), service_path)}'
        )


def get_param_str_from_operation(op_name, service_model):
    operation_model: OperationModel = service_model.operation_model(op_name)
    input_shape = operation_model.input_shape
    parameters = input_shape.members if input_shape else {}
    param_str = get_parameter_declaration_with(parameters, parameters.keys())
    return param_str
