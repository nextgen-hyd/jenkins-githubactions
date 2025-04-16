import yaml

class GithubActionsManager:
    def __init__(self, result_dict,file):
        """
        Initialize the github_actions.yml file with the given base structure.
        """
        #self.file_path = ".github/workflows/github_actions.yml"
        self.file_path = str(file)+'.yaml'
        print(file)
        self.base_structure = {
            "name": "CI/CD Pipeline",
            "on": {
                "push": {
                    "branches": [result_dict["branch"]]
                }
            },
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": []
                }
            }
        }
        # Write the base structure to the file
        self._write_to_file(self.base_structure)

    def _write_to_file(self, content):
        """
        Write the YAML content to the github_actions.yml file.
        """
        with open(self.file_path, "w") as file:
            yaml.dump(content, file, sort_keys=False, default_flow_style=False)

    def _read_from_file(self):
        """
        Read the current YAML content from the file.
        """
        with open(self.file_path, "r") as file:
            return yaml.safe_load(file)

    def append_to_file(self, step_content):
        """
        Append a new step to the build job in the github_actions.yml file.
        """
        #import pdb;pdb.set_trace()
        current_content = self._read_from_file()
        current_content["jobs"]["build"]["steps"].append(step_content)
        self._write_to_file(current_content)
    
    def append_to_job(self, key, content):
        """
        Append a new job to the github_actions.yml file.
        """
        current_content = self._read_from_file()
        current_content["jobs"][key] = content
        self._write_to_file(current_content)
