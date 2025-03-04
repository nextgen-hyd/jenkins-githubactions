import re
import yaml
from github_actions_manager import GithubActionsManager
import shared_library_handler



def handle_git_stage(stage, parameters):
    print("Handling Git stage:")
    
    splitted = stage["content"].lstrip().split(" ")
    main_content = [
        i for i in splitted if i not in ["steps", "{\n", "}\n", ""]
    ]
    dic = {}
    for i in main_content:
        if i in ['git']:
            dic['name'] = "git"
        elif i == 'branch:':
            
            if "${" in main_content[main_content.index(i)+1]:
                branch = re.search(r"\$\{params\.branch\}", main_content[main_content.index(i)+1]).group(0)
                dic['branch'] = branch
            else:
                dic['branch'] = main_content[main_content.index(i)+1]
        elif i == 'url:' :
            if "${" in main_content[main_content.index(i)+1]:
                url = re.search(r"\$\{params\.sourceCode_url\}", main_content[main_content.index(i)+1]).group(0)
                dic['url'] = url
            else:
                dic['url'] = main_content[main_content.index(i)+1]
            
        elif i == 'credentialsId:' :
            if "${" in main_content[main_content.index(i)+1]:
                token = re.search(r"\$\{params\.credentialsId\}", main_content[main_content.index(i)+1]).group(0)
                dic['token'] = token
            else:
                dic['token'] = main_content[main_content.index(i)+1]

    for key, value in dic.items():
        if 'params.' in str(value):  # Check if the value references a param
            param_name = value.split('params.')[1].strip('${}').strip()  # Extract param name
            # Find the corresponding parameter in 'parameters'
            matching_param = next((param for param in parameters if param['name'] == param_name), None)
            if matching_param and 'defaultValue' in matching_param:  # Check if defaultValue exists
                dic[key] = matching_param['defaultValue']  # Replace value in dic
   
    print(dic)
    url1 = dic['url']
    match = re.search(r"github\.com/(.*?)(\.git)?$", url1)
    if 'token' not in dic.keys():
        dic['token'] = None
    #import pdb; pdb.set_trace()
    if match:
        extracted_part = match.group(1)
        dic['url'] = extracted_part

    return {
        "name": "Checkout code",
        "uses": "actions/checkout@v2",
        "with": {
            "repository": "DaggupatiPavan/java-web-app-docker",
            #"token": f"${{ secrets.{dic['token']} }}",
            #"ref": dic["branch"],
        },
    }

from yaml.representer import Representer

# Define a custom representer for multiline strings
def literal_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

def handle_build_stage(stage):
    print("Handling Build stage:") 
    stage_name = stage.get('stage_name', 'Unnamed Stage')
    content = stage.get('content', '')
    print(stage["content"])
    commands = ["#!/bin/bash"]
    maven_content = None
    for line in content.split('\n'):
        line = line.strip()
        match = re.match(r"sh '(.*)'", line) or re.match(r'sh "(.*)"', line)
        if line.startswith("withMaven("):
            maven_content = {"name": "setup JDK for Maven","uses": "actions/setup-java@v3","with":{"java-version": 11, "distribution": "adopt"}}
        if match:
            commands.append(match.group(1))

    
    #yaml.add_representer(str, literal_representer)
    yaml_content = {
    "name": "Build and Deploy",
    "run":  "\n".join(commands) 
    }
    print(yaml_content)

    yaml_str = yaml.dump([yaml_content], default_flow_style=False, sort_keys=False)

    # Print the generated YAML for validation
    print(yaml_str)
    #yaml.representer.SafeRepresenter.add_representer(str, yaml.representer.SafeRepresenter.represent_str)

    #import pdb;pdb.set_trace()
    maven_cmd_content = {
        'name': stage["stage_name"],
        'run':  "\n".join(commands)
    }

    if type(maven_content)==dict and type(maven_cmd_content)==dict:
        return maven_content,maven_cmd_content
    else:
        return maven_cmd_content


def handle_sonarqube_stage(stage):
    #import pdb;pdb.set_trace()
    print("Handling SonarQube stage:")  
    print(stage["content"])

    content = stage.get('content', '')

    commands = ["#!/bin/bash"]
    for line in content.split('\n'):
        line = line.strip()
        match = re.match(r"sh '(.*)'", line) or re.match(r'sh "(.*)"', line)
        if line.startswith("withSonar"):
            sonar_content = {"name": "Set up SonarQube environment", "uses": "sonarsource/sonarqube-scan-action@v1.0","with": {"sonarQubeEnv": {"credentialsId": "sonarQube","installationName": "QualityChecks"}}}

        if match:
            commands.append(match.group(1))

    sonar_cmd_content =  {
            'name': stage["stage_name"],
            'run': "\n".join(commands)
            }
    if sonar_content and sonar_cmd_content:
        return sonar_content,sonar_cmd_content



def handle_docker_stage(stage):
    print("Handling Docker stage:")
    print(stage["content"]) 
    
    content = stage.get('content', '')
    commands = ["#!/bin/bash"]
    #import pdb;pdb.set_trace()

    for line in content.split('\n'):
        line = line.strip()
        match = re.match(r"sh '(.*)'", line) or re.match(r'sh "(.*)"', line)
        if match:
            commands.append(match.group(1))
    

    return {
            'name': stage["stage_name"],
            'run': "\n".join(commands)
            }

    
def handle_kubernetes_stage(stage):

    def handle_kubernetes_plugin(content):
        #import pdb;pdb.set_trace()
        for line in content.split('\n'):
            line = line.strip()
            configs = re.match(r"configs: '(.*)'", line)
            if configs:
                config = configs.group(1)

        kubernetes_content = {"name": "Deploy to Kubernetes","uses": "azure/k8s-deploy@v4","with": {"namespace": "default","manifests": config},"env": {"KUBECONFIG": "${{ secrets.KUBECONFIG}}"}}

        return kubernetes_content

    print("Handling Kubernetes stage : ")
    print(stage["content"])

    content = stage.get('content', '')

    # Extract the command from the content, handling 'script' blocks as well
    commands = ["#!/bin/bash"]

    for line in content.split('\n'):
        line = line.strip()
        match = re.match(r"sh '(.*)'", line) or re.match(r'sh "(.*)"', line)
        if match:
            commands.append(match.group(1))
        elif "kubernetesDeploy(" in line:
            k8s_content = handle_kubernetes_plugin(content)
            
            return k8s_content
    

    return {
            'name': stage["stage_name"],
            'run': "\n".join(commands)
            }


def handle_sh_stages(stage):
    print("Handling sh stage")
    print(stage["content"])

    content = stage.get('content', '')
    commands = ["#!/bin/bash"]

    # Extract multi-line and single-line sh commands
    sh_matches = re.findall(r"sh\s+['\"]{3}([\s\S]*?)['\"]{3}|sh\s+['\"](.*?)['\"]", content)

    for match in sh_matches:
        multi_line, single_line = match
        command = multi_line if multi_line else single_line
        if command:
            commands.append(command.strip())

    return {
        'name': stage["stage_name"],
        'run': "\n".join(commands)
    }


def extract_parameters(file_path):
    parameters = []
    with open(file_path, "r") as file:
        inside_parameters_block = False
        for line in file:
            if "parameters {" in line:
                inside_parameters_block = True
            elif inside_parameters_block and "}" in line:
                inside_parameters_block = False
            elif inside_parameters_block:
                param_line = line.strip()
                param_dict = {}
                if param_line.startswith("string("):
                    param_dict["type"] = "string"
                elif param_line.startswith("choice("):
                    param_dict["type"] = "choice"
                # Extract name and description
                name = param_line.split("name: '")[1].split("',")[0]
                description = param_line.split("description: '")[1].split("'")[0]
                if "defaultValue" in param_line:
                    defaultValue = param_line.split("defaultValue: '")[1].split("'")[0]
                    param_dict["defaultValue"] = defaultValue
                param_dict["name"] = name
                param_dict["description"] = description
                parameters.append(param_dict)
    return parameters


def implementing_shared_libraries(shared_library_directory):
    print("The pipeline has shared libraries")
    slf = shared_library_handler.library_handler(shared_library_directory)
    return slf


"""
if __name__ == "__main__":
"""

def parse_jenkinsfile(file,shared_library_directory):
    #with open("./Jenkinsfile_complex.groovy", "r") as file:
    file_name = file
    
    with open(file,"r") as file:
        stage_list = []
        current_stage = {}
        current_content = []
        in_stage = False
        shared_library_files = []

        for line in file:
            stripped_line = line.lstrip()

            if stripped_line.startswith("@Library"):
                slr = implementing_shared_libraries(shared_library_directory)
                shared_library_files.append(slr)

            if stripped_line.lower().startswith("stage("):
                if in_stage:
                    steps_block = []
                    inside_steps = False
                    for content_line in current_content:
                        content_stripped = content_line.lstrip()
                        if content_stripped.startswith("steps {"):
                            inside_steps = True
                        if inside_steps:
                            steps_block.append(content_line)
                        if inside_steps and content_stripped.startswith("}"):
                            inside_steps = False

                    current_stage["content"] = "".join(steps_block)
                    stage_list.append(current_stage)
                    current_content = []

                stage_name = stripped_line.split("(")[1].split(")")[0].strip("'\"")
                current_stage = {"stage_name": stage_name}
                in_stage = True

            if in_stage:
                current_content.append(line)

        if in_stage and current_stage:
            steps_block = []
            inside_steps = False
            for content_line in current_content:
                content_stripped = content_line.lstrip()
                if content_stripped.startswith("steps {"):
                    inside_steps = True
                if inside_steps:
                    steps_block.append(content_line)
                if inside_steps and content_stripped.startswith("}"):
                    inside_steps = False

            current_stage["content"] = "".join(steps_block)
            stage_list.append(current_stage)

    parameters = extract_parameters(file_name)

    manager = GithubActionsManager({"branch": "main"},file_name)

    for stage in stage_list:
        stage_name = stage["stage_name"].lower()

        if any(item in stage['content'] for item in shared_library_files):
            content = stage['content'].strip()
            match = re.search(r'script\s*\{(.*?)\}', content, re.DOTALL)
            if match:
                script_content = match.group(1).strip()
                print("Script content:", script_content)
            else:
                print("No script block found")
            #import pdb;pdb.set_trace()
            library_name = script_content.split('.')[0]
            function_name = script_content.split('.')[-1]
            shared_library_content = shared_library_handler.library_snippet_generator(library_name,function_name)
            manager.append_to_file(shared_library_content)
            
        elif "git" in stage["content"]:
            
            git_step = handle_git_stage(stage, parameters)
            manager.append_to_file(git_step)

        elif "mvn" in stage["content"]:
            if "mvn" in stage["content"] and "withSonarQubeEnv" in stage["content"]:
                all_sonar_contents = []
                sonar_content, sonar_cmd_content = handle_sonarqube_stage(stage)
                all_sonar_contents.append(sonar_content)
                all_sonar_contents.append(sonar_cmd_content)
                for content in all_sonar_contents:
                    manager.append_to_file(content)
            else:
                #import pdb;pdb.set_trace()
                all_maven_contents = []
                maven = handle_build_stage(stage)
                if type(maven)==tuple:
                    for content in  maven:
                        all_maven_contents.append(content)
                elif type(maven)==dict:
                    all_maven_contents.append(maven)
                for content in all_maven_contents:                   
                    manager.append_to_file(content)      

        elif "docker build " in stage["content"] or ">> Dockerfile" in stage["content"] :
            docker_step = handle_docker_stage(stage)
            manager.append_to_file(docker_step)
        
        elif "docker push " in stage["content"] :
            docker_step = handle_docker_stage(stage)
            docker_login_content = {
            "name": "Log in to Docker Hub",
            "uses": "docker/login-action@v2",
            "with": {
            "username": "${{ secrets.DOCKER_USERNAME }}",
            "password": "${{ secrets.DOCKER_PASSWORD }}"
            }
            }
            manager.append_to_file(docker_login_content)
            manager.append_to_file(docker_step)
        
        elif  "kubernetesDeploy(" in stage["content"]:
            kube_step = handle_kubernetes_stage(stage)
            manager.append_to_file(kube_step)
        elif " sh " in stage["content"]:
            #import pdb;pdb.set_trace()
            shell = handle_sh_stages(stage)
            manager.append_to_file(shell)
        else:
            print(f"No specific handler for stage: {stage['stage_name']}\n")



    