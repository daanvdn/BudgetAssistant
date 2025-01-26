from drf_spectacular.openapi import AutoSchema




def custom_schema_postprocessor(result, generator, request, public):
    from pybackend.rules import RuleSerializer
    resolved = AutoSchema().resolve_serializer(serializer=RuleSerializer, direction='request', bypass_extensions=False)
    result['components']['schemas']['Rule'] = generator.get_serializer_schema(RuleSerializer)
    return result