class PomParser:
    def __init__(self, pom_file_path):
        self.pom_file_path = pom_file_path
        self.dependencies = []

    def parse(self):
        import xml.etree.ElementTree as ET

        tree = ET.parse(self.pom_file_path)
        root = tree.getroot()

        # Define the namespace
        namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}

        # Extract dependencies
        for dependency in root.findall('maven:dependencies/maven:dependency', namespace):
            group_id = dependency.find('maven:groupId', namespace).text
            artifact_id = dependency.find('maven:artifactId', namespace).text
            version = dependency.find('maven:version', namespace).text if dependency.find('maven:version', namespace) is not None else None
            
            self.dependencies.append({
                'group_id': group_id,
                'artifact_id': artifact_id,
                'version': version
            })

    def get_dependencies(self):
        return self.dependencies