class TechComponent:
    def __init__(self, name, version, component_type):
        self.name = name
        self.version = version
        self.component_type = component_type

    def __repr__(self):
        return f"TechComponent(name={self.name}, version={self.version}, type={self.component_type})"

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "type": self.component_type
        }