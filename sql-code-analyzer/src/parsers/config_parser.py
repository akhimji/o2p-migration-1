class ConfigParser:
    def __init__(self, config_files):
        self.config_files = config_files
        self.weblogic_detected = False

    def parse(self):
        for config_file in self.config_files:
            self.detect_weblogic(config_file)

    def detect_weblogic(self, config_file):
        # Logic to detect WebLogic usage in the provided config file
        with open(config_file, 'r') as file:
            content = file.read()
            if 'weblogic' in content.lower():
                self.weblogic_detected = True

    def is_weblogic_used(self):
        return self.weblogic_detected