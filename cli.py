# bead/cli.py
import os
import sys
import argparse
import shutil
from bead.server.dev_server import start_dev_server

# This command-line interface is the top-level CLI for the project.
# It includes commands like `bead create`, `bead dev`, etc.

def create_project(project_name):
    """
    Creates a new Bead project.
    """
    current_dir = os.getcwd()
    project_path = os.path.join(current_dir, project_name)

    if os.path.exists(project_path):
        print(f"Error: A folder named '{project_name}' already exists.")
        return

    print(f"Creating project '{project_name}'...")
    
    # Create project folders
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "pages"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "components"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "public"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "pages", "api"), exist_ok=True)

    # Copy bead.png file
    # Find the framework's root directory
    framework_root = os.path.dirname(os.path.abspath(__file__))
    source_image_path = os.path.join(framework_root, "bead.png")
    destination_image_path = os.path.join(project_path, "public", "bead.png")

    if os.path.exists(source_image_path):
        try:
            shutil.copyfile(source_image_path, destination_image_path)
            print("INFO: 'bead.png' logo copied to the project.")
        except IOError as e:
            print(f"WARNING: An error occurred while copying 'bead.png': {e}")
    else:
        print("WARNING: 'bead.png' file not found. Please ensure it's in the root directory of the Bead framework.")

    # Create the new index page content
    index_content = """from bead.ui import Page, Text, Card, Stack, Link, Image

def default(params, context):
    return Page(
        title="Bead Framework",
        body=[
            Card(
                style="max-w-xl mx-auto mt-12 p-6 bg-white flex flex-col items-center",
                children=[
                    Image(src="/public/bead.png", alt="Bead Framework Logo", style="w-48 h-24 mb-4"),
                    Text("Build modern web UI entirely with Python!",
                         style="text-2xl font-bold text-gray-800 text-center font-inter"),
                    Text("No HTML or CSS needed; just use Python.",
                         style="text-gray-600 mt-2 text-center font-inter"),
                    Link("Find More!", href="https://github.com/codeyevsky/bead", 
                         style="mt-6 font-medium text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg no-underline"),
                ]
            )
        ]
    )
"""
    # Create the InfoCard component
    infocard_content = """from bead.ui import Card, Text

def InfoCard(title: str, body: str):
    return Card(style="p-4 rounded-xl bg-gray-50 border border-gray-200", children=[
        Text(title, style="font-semibold text-gray-800"),
        Text(body, style="text-gray-600 mt-1")
    ])
"""
    
    # Create the API handler
    api_handler_content = """def handler(request):
    user_agent = request.headers.get("user-agent", "?")
    return {"ok": True, "message": f"Hello! User-Agent: {user_agent}"}
"""

    # Create basic project files
    with open(os.path.join(project_path, "app.py"), "w", encoding="utf-8") as f:
        f.write("# Main application file for the Bead project")

    with open(os.path.join(project_path, "bead.config.json"), "w", encoding="utf-8") as f:
        f.write('{\n  "server": { "port": 3000 }\n}')
        
    with open(os.path.join(project_path, "pages", "index.bead"), "w", encoding="utf-8") as f:
        f.write(index_content)

    with open(os.path.join(project_path, "components", "infocard.bead"), "w", encoding="utf-8") as f:
        f.write(infocard_content)
        
    with open(os.path.join(project_path, "pages", "api", "helloClick.py"), "w", encoding="utf-8") as f:
        f.write(api_handler_content)
        
    # Create run.py and requirements.txt to simplify the developer experience
    with open(os.path.join(project_path, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("# Required dependencies for the Bead framework.\n")
        f.write("uvicorn\n")
        f.write("starlette\n")
        f.write("itsdangerous\n")
        f.write("watchdog\n")
        f.write("-e ../bead\n")
    
    with open(os.path.join(project_path, "run.py"), "w", encoding="utf-8") as f:
        f.write("import os\n")
        f.write("import sys\n")
        f.write("\n")
        f.write("script_dir = os.path.dirname(os.path.abspath(__file__))\n")
        f.write("parent_dir = os.path.dirname(script_dir)\n")
        f.write("sys.path.insert(0, parent_dir)\n")
        f.write("\n")
        f.write("import bead.cli\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    sys.argv = ['bead', 'dev', '.']\n")
        f.write("    bead.cli.main()\n")

    print(f"'{project_name}' project created successfully!")
    print("--------------------------------------------------")
    print(f"To run your project:")
    print(f"1. Navigate to your project directory with 'cd {project_name}'.")
    print(f"2. Run 'pip install -r requirements.txt' to install dependencies.")
    print(f"3. Start the server with 'python run.py'.")
    print("--------------------------------------------------")


def main():
    """
    The main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description="Bead Framework CLI")
    
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Creates a new Bead project.")
    create_parser.add_argument("project_name", help="The name of the project to create.")
    
    # The `bead dev` command now takes the project folder as an argument
    dev_parser = subparsers.add_parser("dev", help="Starts the development server.")
    dev_parser.add_argument("project_path", nargs="?", default=".", help="The path to the project directory.")

    args = parser.parse_args()
    
    # If the `start_dev_server` function was not imported before
    # We ensure that the dev command can properly locate the project folder
    if args.command == "create":
        create_project(args.project_name)
    elif args.command == "dev":
        start_dev_server(os.path.abspath(args.project_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()