import yaml

with open("../environment.yml", "r") as file:
    env_data = yaml.safe_load(file)

# Extract pip dependencies
pip_packages = []
for dep in env_data.get("dependencies", []):
    if isinstance(dep, dict) and "pip" in dep:
        pip_packages = dep["pip"]

with open("../pip_packages.txt", "w", encoding='utf-8') as file:
    file.write("\n".join(pip_packages))

