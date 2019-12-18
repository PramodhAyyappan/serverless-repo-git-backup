#!/usr/bin/env python
import os
import json
import base64
import hashlib
import hmac
import requests
from git import Repo
import boto3
import shutil

# Get the SSM Parameter Keys
try:
    GIT_TOKEN_SSM_PARAMETER_KEY = os.getenv('GIT_TOKEN_SSM_PARAMETER_KEY')
except Exception:
    GIT_TOKEN_SSM_PARAMETER_KEY = '/GitHub/Token/PramodhAyyappan'

# Get ssm module
ssm = boto3.client('ssm')

gitUser = format(ssm.get_parameter(Name=GIT_TOKEN_SSM_PARAMETER_KEY, WithDecryption=True)['Parameter']['Name'])
gitToken = format(ssm.get_parameter(Name=GIT_TOKEN_SSM_PARAMETER_KEY, WithDecryption=True)['Parameter']['Value'])


client = boto3.client('codecommit')
os.environ['HOME'] = '/var/task'
gitOrgOrUser = os.getenv('GIT_ORG_OR_USER')
gitHubUrl = 'https://{}:{}@github.com/{}'.format(gitUser.split('/')[3], gitToken, gitOrgOrUser)

def clone(repoName):
    """
    Retrieves or Creates Code Commit Repository
    :param repoName: Github Repository Name
    :return: returns nothing
    """
    localDir = f'/tmp/{repoName}'
    try:
        shutil.rmtree(localDir)
    except:
        pass
    repoUrl = f"{gitHubUrl}/{repoName}.git"
    localRepo = Repo.clone_from(repoUrl, localDir)
    print(f'Cloned repo: {repoName}')
    remoteRepo = getOrCreateRepo(repoName)
    print("Created remote repo")
    remote = localRepo.create_remote(name=remoteRepo['repositoryName'], url=remoteRepo['cloneUrlHttp'])
    print('Created remote')
    remote.push(refspec='master:master')
    print('Pushed to master')


def getOrCreateRepo(repoName):
    """
    Retrieves or Creates Code Commit Repository
    :param repoName: Github Repository Name
    :return: returns Code Commit Repo metadata
    """
    try:
        codeCommitRepo = client.get_repository(repositoryName=repoName)
    except client.exceptions.RepositoryDoesNotExistException:
        codeCommitRepo = client.create_repository(repositoryName=repoName)
    except:
        print("Error accessing CodeCommit Service!!!")
        raise Exception("Error accessing CodeCommit Service!!!")
    print(codeCommitRepo)
    return codeCommitRepo['repositoryMetadata']


# Verify the webhook signature
def verify_signature(secret, signature, payload):
    """
    Retrives Github Webhook Payload information from APIGateway and verify the signature.
    :param secret: Github Webhook Secret
    :param signature: Github Webhook Signature
    :param payload: Github Webhook payload data
    :return: returns true or false
    """
    computed_hash = hmac.new(secret.encode('ascii'), payload, hashlib.sha1)
    computed_signature = '='.join(['sha1', computed_hash.hexdigest()])
    return hmac.compare_digest(computed_signature.encode('ascii'), signature.encode('ascii'))


def lambda_handler(event, context):
    """
    Extracts Github Webhook Payload information and backup repo to CodeCommit.
    :param event: Event data from API Gateway contains Github Webhook Payload
    :param context: This object provides methods and properties that provide information about the invocation, function, and execution environment
    :return: returns nothing
    """
    event['payload'] = base64.b64decode(event['payload'])
    verified = verify_signature(event['secret'],
                                event['x_hub_signature'],
                                event['payload'])
    print('Signature verified: {}'.format(verified))
    if(verified):
        payload = json.loads(event['payload'])
        # Condition on the Basis of Event
        git_event = event['x_github_event']
        if (git_event == 'push'):
            if(payload['ref'] == 'refs/heads/master'):
                repoName = payload['repository']['name']
                print(repoName)
                clone(repoName)
            else:
                print("No updates in Master brannch for this repo {}".format(payload['repository']['name']))
