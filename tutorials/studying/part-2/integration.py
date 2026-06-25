import json
import requests

def integration_get_route(
    address: str,
    port: str,
    route_type: str,
    route_name: str,
    path_replacers: any,
    path_names: any
): 
    url_prefix = 'http://' + address + ':' + port

    routes = {
        'logs': 'GET:/general/logs',
        'setup': 'POST:/setup/config'
    }

    route = None
    if route_name in routes:
        i = 0
        route = routes[route_name].split('/')
        for name in route:
            if name in path_replacers:
                replacer = path_replacers[name]
                if 0 < len(replacer):
                    route[i] = replacer
            i = i + 1

        if not len(path_names) == 0:
            route.extend(path_names)

        if not len(route_type) == 0:
            route[0] = route_type + ':'
        
        route = '/'.join(route)
    print('Used route: ' + str(route))
    route_split = route.split(':')
    url_type = route_split[0]
    used_path = route_split[1]
    full_url = url_prefix + used_path
    return url_type, full_url

def integration_request_route(
    address: str,
    port: str,
    route_type: str,
    route_name: str,
    path_replacers: any,
    path_names: any,
    route_input: any,
    timeout: any
) -> any:
    url_type, full_url = integration_get_route(
        address = address,
        port = port,
        route_type = route_type,
        route_name = route_name,
        path_replacers = path_replacers,
        path_names = path_names
    )

    if url_type == 'POST':
        route_response = requests.post(
            url = full_url,
            json = route_input,
            timeout = timeout
        )
    if url_type == 'GET':
        route_response = requests.get(
            url = full_url,
            json = route_input,
            timeout = timeout
        )
    
    route_status_code = None
    route_returned_text = {}
    if not route_response is None:
        route_status_code = route_response.status_code
        if route_status_code == 200:
            route_returned_text = json.loads(route_response.text)
    return route_status_code, route_returned_text