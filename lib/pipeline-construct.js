const { PolicyStatement } = require("@aws-cdk/aws-iam");
const { Construct, Duration, Stack } = require("@aws-cdk/core");
const {
  Project,
  BuildSpec,
  EventAction,
  LinuxBuildImage,
  Source,
  FilterGroup
} = require("@aws-cdk/aws-codebuild");

class PipelineConstruct extends Construct {
  constructor(scope, bucket, distribution) {
    super(scope, "pipeline");
    let commands = [
      "cdk bootstrap",
      "pipenv run python main.py",
      `aws s3 cp --acl public-read --recursive docs/ s3://${bucket.bucketName}`,
      "cdk diff || true",
      "cdk deploy"
    ];
    if (distribution) {
      commands.push(
        `aws cloudfront create-invalidation --distribution-id ${distribution} --paths "/*"`
      );
    }
    let project = new Project(this, "deploy-site", {
      description: "Deploys website at botodocs.com",
      timeout: Duration.minutes(30),
      badge: true,
      source: Source.gitHub({
        cloneDepth: 1,
        owner: "jeshan",
        repo: "botodocs",
        webhookFilters: [
          FilterGroup.inEventOf([EventAction.PUSH]).andBranchIs("master")
        ]
      }),
      environment: { buildImage: LinuxBuildImage.STANDARD_2_0 },
      buildSpec: BuildSpec.fromObject({
        version: "0.2",
        phases: {
          install: {
            "runtime-versions": {
              nodejs: "12",
              python: "3.7"
            }
          },
          pre_build: {
            commands: ["npm i -g aws-cdk@1.34.1", "npm i", "pip install pipenv"]
          },
          build: {
            commands
          }
        }
      })
    });
    let { account, region, stackName } = Stack.of(this);
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [
          `arn:aws:cloudformation:${region}:${account}:stack/CDKToolkit/*`,
          `arn:aws:cloudformation:${region}:${account}:stack/${stackName}*/*`
        ],
        actions: [
          "cloudformation:DescribeStacks",
          "cloudformation:GetTemplate",
          "cloudformation:CreateChangeSet",
          "cloudformation:DescribeChangeSet",
          "cloudformation:ExecuteChangeSet",
          "cloudformation:DescribeStackEvents",
          "cloudformation:DeleteChangeSet",
          "cloudformation:DeleteStack"
        ]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [`arn:aws:iam::${account}:role/${stackName}*`],
        actions: [
          "iam:CreateRole",
          "iam:GetRole",
          "iam:PassRole",
          "iam:UpdateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy"
        ]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: ["*"],
        actions: ["acm:RequestCertificate"]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [`arn:aws:acm:${region}:${account}:certificate/*`],
        actions: ["acm:DeleteCertificate", "acm:DescribeCertificate"]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [
          `arn:aws:s3:::${stackName}*`,
          "arn:aws:s3:::cdktoolkit-stagingbucket-*"
        ],
        actions: [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:PutBucketWebsite",
          "s3:GetBucketPolicy",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy",
          "s3:PutEncryptionConfiguration",
          "s3:PutBucketPublicAccessBlock",
          "s3:*Object",
          "s3:ListBucket"
        ]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [
          `arn:aws:codebuild:${region}:${account}:project/pipelinedeploysite*`
        ],
        actions: [
          "codebuild:CreateProject",
          "codebuild:UpdateProject",
          "codebuild:DeleteProject",
          "codebuild:CreateWebhook",
          "codebuild:UpdateWebhook",
          "codebuild:DeleteWebhook"
        ]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: ["*"],
        actions: ["cloudfront:*CloudFrontOriginAccessIdentity*"]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [
          `arn:aws:lambda:${region}:${account}:function:${stackName}*`
        ],
        actions: ["lambda:*Function*"]
      })
    );
    project.addToRolePolicy(
      new PolicyStatement({
        resources: [`arn:aws:cloudfront::${account}:distribution/*`],
        actions: ["cloudfront:*Distribution*", "cloudfront:*agResource"]
      })
    );
  }
}

module.exports = { PipelineConstruct };