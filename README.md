# botodocs: a (hopefully) better boto3 doc site

![](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiOXRZbVgzbnltSnowWGR2TVF3cDlqNEZPUjRXS2NLSVVLUjc2T0hJeWtwYlBSUUpyU1owZVFPRUFuVndadDk4TjVMSXFQQmhhRFIrYzRmc0QvSFJ2TVFRPSIsIml2UGFyYW1ldGVyU3BlYyI6Im82eXdQRTYxMzdmY1Y1czEiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)


> Visit https://botodocs.com

# Why
I thought that the official docs has a lot of room to improve, so I built a "better" site in the meantime.

# Features
- lots of caching
- better navigation
- fast to load
- shorter pages

# Note to forkers:
This project uses docsify to convert the markdown files into a simple static website.

- `npm i docsify-cli -g`
- run `pipenv run python main.py` to generate the pages and serve a website (note that it calls `docsify serve docs` behind the scenes)
- Open browser at http://localhost:3000
- Edits to static files will be reloaded live. Otherwise rerun main.py for dynamic pages.

## Deploying on AWS
Uses the AWS CDK. See [lib/pipeline-construct.js](lib/pipeline-construct.js) for details on the deployment pipeline.
- `npm i -g aws-cdk`
- `cdk deploy`

This is what the CDK will deploy:

![](/diagram.png)

# Legal
Released under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

https://creativecommons.org/licenses/by-nc-sa/4.0/

Project is based on boto3. Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. Licensed Apache Licence 2.0. See file [original-LICENCE](original-LICENCE) for details
