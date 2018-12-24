from __future__ import print_function
import requests
from requests import get
import subprocess
import re
import sys
from requests.auth import HTTPBasicAuth
import pandas as pd
import time
from tqdm import tqdm

uname = 'bettermanzzy'

def proc(cmd_args, pipe=True, dummy=False):
    if dummy:
        return
    if pipe:
        subproc = subprocess.Popen(cmd_args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    else:
        subproc = subprocess.Popen(cmd_args)
    return subproc.communicate()

def git(args, pipe=True):
    return proc(['git'] + args, pipe)

def start_requests(url):
    #print('getting', url)
    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': 'token d1e20c381ba7dd8bc6627c319fde0bdf95830ac8',
               'Content-Type': 'application/json',
               'Accept': 'application/json'
               }
    return requests.get(url, headers=headers)

def findEmailFromContributor(username, repo, contributor):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': 'token d1e20c381ba7dd8bc6627c319fde0bdf95830ac8',
               'Content-Type': 'application/json',
               'Accept': 'application/json'
               }
    response = get('https://github.com/%s/%s/commits?author=%s' % (username, repo, contributor), auth=HTTPBasicAuth(uname, ''),headers=headers).text
    latestCommit = re.search(r'href="/%s/%s/commit/(.*?)"' % (username, repo), response)
    if latestCommit:
        latestCommit = latestCommit.group(1)
    else:
        latestCommit = 'dummy'
    #print(latestCommit)
    commitDetails = get('https://github.com/%s/%s/commit/%s.patch' % (username, repo, latestCommit), auth=HTTPBasicAuth(uname, ''),headers=headers).text
    commitStr = commitDetails.encode('utf8')
    email_list = re.findall(r'<(.*)>', commitStr)
    if len(email_list) >= 1:
        email = email_list[0]

    return email
if __name__ == '__main__':

    sys_url = None
    if len(sys.argv) >= 2:
        sys_url = sys.argv[1]
    else:
        print("Your input is error,please try again")
        sys.exit(0)

    try:
        git_name = sys_url.split('github.com/')[1]
        xlsx_name_list = git_name.split('/')
    except:
        print("Your input is error,please try again")
        sys.exit(0)

    username = None
    xlsx_name = None
    if len(xlsx_name_list)>=2:
        xlsx_name = xlsx_name_list[1]
        username = xlsx_name_list[0]
    else:
        print("Your input is error,please try again")
        sys.exit(0)

    url = 'https://api.github.com/repos/' + username + '/' + xlsx_name + '/' + 'contributors'
    get_url = start_requests(url)
    get_data = get_url.json()
    print('the numbers of contributors : ',len(get_data))
    print('Begin to count the message of contributors:')

    name_git = []
    id_git = []
    email_git = []
    location_git = []
    company_git = []
    project_git = []
    commits_git = []
    follower_git = []
    try:
        for data in tqdm(get_data,ncols=120):
            id = data['login']
            emails = []
            email = findEmailFromContributor(username , xlsx_name , id)
            emails.append(email)
            commits = data['contributions']
            msg_url = data['url']
            get_msg = start_requests(msg_url).json()
            name = get_msg['name']
            if name is None:
                name = id
            company = get_msg['company']
            location = get_msg['location']
            email1 = get_msg['email']

            if email1 != email and email1 is not None:
                emails.append(email1.encode('utf8'))
            project = get_msg['public_repos']
            follower = get_msg['followers']

            name_git.append(name)
            id_git.append(id)
            email_git.append(emails)
            location_git.append(location)
            company_git.append(company)
            commits_git.append(commits)
            project_git.append(project)
            follower_git.append(follower)

            time.sleep(0.01)
    except:
        print('Appear an error,please checkout your input is a github_repos_url! Correct input should like "https://github.com/lz4/lz4"')

    # write data to git_name.csv file
    dict = {'name': name_git ,'githubID':id_git ,'email':email_git ,'location':location_git ,'company':company_git ,'commits':commits_git ,'project':project_git ,'followers':follower_git}

    writer = pd.ExcelWriter(xlsx_name + '.xlsx')
    df = pd.DataFrame(dict)
    df.to_excel(writer, columns=['name','githubID','email','location','company','commits','project','followers'], index=False, encoding='utf-8',
                    sheet_name='Sheet')
    writer.save()

