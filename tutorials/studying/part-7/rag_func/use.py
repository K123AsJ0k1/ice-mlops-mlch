def rag_format_context(
    query_results: any,
    wrapper_tag: str,
    metadata_keys: list,
    material_key: str,
    path_key: str,
    content_key: str
) -> any:
    try:
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    collected_context = []
    collected_metrics = []
    root = ET.Element(wrapper_tag)
    for j, (result, metrics) in enumerate(query_results):
        for i, point in enumerate(result, 1):
            query_score = point.score
            query_payload = point.payload

            chunk_attributes = {}
            chunk_attributes['id'] = str(i)
            chunk_attributes['score'] = str(round(query_score,2))
            for metadata_key in metadata_keys:
                chunk_attributes[metadata_key] = str(query_payload.get(metadata_key))

            chunk_elem = ET.SubElement(root, "chunk", attrib = chunk_attributes)

            reference_material = query_payload.get(material_key)
            if reference_material:
                material_attributes = {}
                for key, value in reference_material.items():
                    key_split = key.split('|')
                    material_tag = key_split[0]
                    value_type = key_split[1]

                    if not material_tag in material_attributes:
                        material_attributes[material_tag] = {
                            'tag': material_tag
                        }

                    material_attributes[material_tag][value_type] = value

                materials = list(material_attributes.values())
                for item in materials:
                    ET.SubElement(chunk_elem, "reference-material", attrib = item)

            reference_paths = query_payload.get(path_key)
            if reference_paths:
                path_attributes = {}
                id = 1
                for key, value in reference_paths.items():
                    if not id in path_attributes:
                        path_attributes[id] = {
                            'id': str(id)
                        }
                    path_attributes[id]['relative-path'] = key
                    path_attributes[id]['absolute-path'] = value
                    id += 1
                    
                paths = list(path_attributes.values())
                for item in paths:
                    ET.SubElement(chunk_elem, "reference-path", attrib = item)

            content_elem = ET.SubElement(chunk_elem, "content")
            # Use \n{query_payload.get(content_key)}\n for presentation
            query_content = query_payload.get(content_key)
            collected_context.append(query_content)
            content_elem.text = str(f'{query_content.replace('\n','').replace('\r','')}')
        metrics['batch-index'] = j
        collected_metrics.append(metrics)

    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    
    # Pretty-print and strip the default <?xml version="1.0"?> declaration header
    formatted_xml = parsed_xml.toprettyxml(indent="")
    xml_lines = formatted_xml.splitlines()
    
    if xml_lines and xml_lines[0].startswith("<?xml"):
        xml_lines = xml_lines[1:]

    formatted_context = "\n".join(xml_lines)
    return collected_context, formatted_context, collected_metrics