#!/usr/bin/env python3

import typing
from github import Github, Auth

from platformdirs import PlatformDirs
import os, json, sys
import subprocess

if os.getenv("USER") != "root":
    print("Must be root, rerun with sudo!")
    sys.exit(1)

DefaultSettings = {
    "access_token": "",
    
    "githubRepo": "",
    "hostname": subprocess.run(['hostname'], stdout=subprocess.PIPE).stdout.decode('utf-8').rstrip("\n")
}

yes = [
    "yes",
    "y",
    "yeah"
]

no = [
    "no",
    "n",
    "nah"
]

dirs = PlatformDirs("nixos-update", "c-gale")
Dir = f"/etc/{dirs.appname}"
SettingsPath = Dir + "/settings.json"

def RunGitCommand(repo_path, args):
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()

def ReadSettings() -> typing.Any:
    global DefaultSettings
    global SettingsPath

    if not os.path.exists(Dir):
        os.mkdir(Dir)

    if not os.path.exists(SettingsPath):
        newFile = open(SettingsPath, "w")
        newFile.writelines(json.dumps(DefaultSettings, indent=2))

        return DefaultSettings
   
    try:
        return json.load(open(SettingsPath, "r"))
    except Exception as e:
        print(e)

def GetRepo(repoName: str, token: str, shouldUpdate: bool) -> bool:
    owner, repo = repoName.split("/") 
    clone_url = f"https://{token}@github.com/{owner}/{repo}.git"
    repo_path = Dir + "/" + repo
   
    RunGitCommand(repo_path, ["fetch", "origin"])
    local_commit = RunGitCommand(repo_path, ["rev-parse", "HEAD"])
    remote_commit = RunGitCommand(repo_path, ["rev-parse", f"origin/main"])

    if local_commit == remote_commit:
        print("✅ Repository is up to date.")
    else:
        if not shouldUpdate:
            return True

        print("⬇️ Pulling changes...")
       
        try:
            RunGitCommand(repo_path, ["remote", "set-url", "origin", clone_url])
            RunGitCommand(repo_path, ["pull"])

            return True
        except Exception as e:
            print(e)

    return False

if __name__ == "__main__":
    user_settings = ReadSettings()
  
    force = False
    if len(sys.argv) > 1: 
        if sys.argv[1] == "-f" or sys.argv[1] == "--force":
            force = True

    auth = Auth.Token(user_settings["access_token"])
    g = Github(auth=auth)

    repo = g.get_repo(user_settings["githubRepo"])
    owner, repoName = user_settings["githubRepo"].split("/") 
    
    clone_url = f"https://{user_settings["access_token"]}@github.com/{owner}/{repo.name}.git"
    
    Cloned = False
    if not os.path.exists(Dir + "/" + repo.name):
        print("Repo does not exist, cloning... (this may take a while)")
        RunGitCommand(Dir + "/", ["clone", clone_url])
        print("Cloned repo")
        Cloned = True

    commit = repo.get_commits().get_page(0)[0].commit

    buildType = "switch"
    if commit.message.lower().find("[boot]") > 0:
        buildType = "boot"
        
    if force:
        subprocess.run(["sudo", "nixos-rebuild", buildType, "--flake", Dir + "/" + repoName + "#" + user_settings["hostname"]])

        if buildType == "boot":
            print("⚠️ You will have to restart to see changes for this update")
        
        sys.exit()

    print("Checking if up to date...")

    Updated = GetRepo(user_settings["githubRepo"], user_settings["access_token"], False)
    if Updated or Cloned:
        commitMSG = {
            f"Author - {commit.author.name}",
            f"Details: \n{commit.message}"
        }

        print("Commit Details:")
        print("###########################")

        for line in commitMSG:
            print(line)

        print("###########################")
        while True:
            buildUpdate = input(f"Do you want to update your current config? (machine name: {user_settings['hostname']}) [y/N] ")

            if yes.__contains__(buildUpdate.lower()):
                print("Updating")
            
                GetRepo(user_settings["githubRepo"], user_settings["access_token"], True)
                subprocess.run(["sudo", "nixos-rebuild", buildType, "--flake", Dir + "/" + repoName + "#" + user_settings["hostname"]])
               
                if buildType == "boot":
                    print("⚠️ You will have to restart to see changes for this update")

                print("Changes complete!")
                break
            elif no.__contains__(buildUpdate.lower()):
                print(f"Exiting...")
                break
            else:
                print("Not a command (ex. yes, yeah, y or no, nah, n)")

    g.close()
