const { Bucket } = require("@aws-cdk/aws-s3");
const {
  CfnCloudFrontOriginAccessIdentity,
  CloudFrontWebDistribution
} = require("@aws-cdk/aws-cloudfront");
const { CanonicalUserPrincipal } = require("@aws-cdk/aws-iam");
const { PipelineConstruct } = require("./pipeline-construct");

const { Stack, RemovalPolicy } = require("@aws-cdk/core");
const {
  Certificate,
  ValidationMethod
} = require("@aws-cdk/aws-certificatemanager");

class CdkStack extends Stack {
  /**
   *
   * @param {cdk.Construct} scope
   */
  constructor(scope) {
    super(scope, "botodocs");

    const domainName = "botodocs.com";
    const cert = new Certificate(this, "cert", {
      domainName,
      validationMethod: ValidationMethod.DNS
    });

    const websiteBucket = new Bucket(this, "WebsiteBucket", {
      domainName,
      removalPolicy: RemovalPolicy.DESTROY,
      websiteIndexDocument: "index.html",
      websiteErrorDocument: "error.html"
    });

    const originId = new CfnCloudFrontOriginAccessIdentity(
      this,
      "OriginAccessIdentity",
      {
        cloudFrontOriginAccessIdentityConfig: {
          comment: `CloudFront OriginAccessIdentity for ${websiteBucket.bucketName}`
        }
      }
    );

    const deployCdn = true; // I made it togglable because cloudfront takes a while to deploy
    if (deployCdn) {
      websiteBucket.grantRead(
        new CanonicalUserPrincipal(originId.attrS3CanonicalUserId)
      );
    } else {
      websiteBucket.grantPublicAccess();
    }

    let s3OriginConfig = {
      originAccessIdentityId: originId.ref,
      s3BucketSource: websiteBucket
    };

    const distributionConfig = {
      originConfigs: [
        {
          s3OriginSource: {
            ...s3OriginConfig
          },
          behaviors: [{ isDefaultBehavior: true }]
        }
      ],
      aliasConfiguration: {
        acmCertRef: cert.certificateArn,
        names: [domainName]
      }
    };
    let distribution;
    if (deployCdn) {
      distribution = new CloudFrontWebDistribution(
        this,
        "WebSiteDistribution",
        distributionConfig
      );
    }

    new PipelineConstruct(this, websiteBucket, distribution);
  }
}

module.exports = { CdkStack };
