#print activating conda environment
echo "Activating conda environment"
conda activate budget-assistant-backend-django
echo "generating openapi schema"
./manage.py spectacular --color --file schema.yml

echo "Generating Angular API"
if (Test-Path .\api)
{
    Remove-Item .\api -Recurse -Force
}

openapi-generator-cli generate -i schema.yml -g typescript-angular -o ./api --additional-properties=modelPropertyNaming=camelCase,fileNaming=kebab-case,enumPropertyNaming=original,ngVersion=14.2.8,npmName=budget-assistant-client