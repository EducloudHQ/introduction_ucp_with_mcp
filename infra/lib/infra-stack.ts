import * as cdk from 'aws-cdk-lib';
import { CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CfnExpressGatewayService, Cluster } from 'aws-cdk-lib/aws-ecs';
import { Vpc } from 'aws-cdk-lib/aws-ec2';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { DockerImageAsset } from 'aws-cdk-lib/aws-ecr-assets';
import * as path from 'path';


export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

  
      // Create VPC for the ECS cluster
      const vpc = new Vpc(this, 'AppVpc', {
        maxAzs: 2,
        enableDnsHostnames: true,
        enableDnsSupport: true,
        natGateways: 1,
        createInternetGateway: true,
        vpcName: 'ucp-mcp-vpc',
      });
  
      // Create ECS Cluster
      const cluster = new Cluster(this, 'AppCluster', {
        vpc: vpc,
        clusterName: 'ucp-mcp-cluster',
        enableFargateCapacityProviders: true,
      });
  
      // Build and push the Docker image automatically using CDK assets
      const asset = new DockerImageAsset(this, 'UcpMcpImage', {
        directory: path.join(__dirname, '..', '..'),
        platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
      });
  
      // Create Task Execution Role
      const taskExecutionRole = new Role(this, 'TaskExecutionRole', {
        assumedBy: new ServicePrincipal('ecs-tasks.amazonaws.com'),
        description: 'ECS Task Execution Role for ucp-mcp',
        managedPolicies: [
          ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy')
        ]
      });
  
      // Create Infrastructure Role
      const infrastructureRole = new Role(this, 'InfrastructureRole', {
        assumedBy: new ServicePrincipal('ecs.amazonaws.com'),
        description: 'ECS Infrastructure Role for Express Gateway Services',
        managedPolicies: [
          ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSInfrastructureRoleforExpressGatewayServices')
        ]
      });
  
      // Create the Express Gateway Service
      const expressService = new CfnExpressGatewayService(this, 'ExpressService', {
        cluster: cluster.clusterName,
        serviceName: 'ucp-mcp-service',
        primaryContainer: {
          image: asset.imageUri,
          containerPort: 8000,
        },
        executionRoleArn: taskExecutionRole.roleArn,
        infrastructureRoleArn: infrastructureRole.roleArn,
        healthCheckPath: '/', 
        scalingTarget: {
          minTaskCount: 1,
          maxTaskCount: 3,
        },
        cpu: '256',
        memory: '512',
      });
  
      // Ensure service depends on cluster
      expressService.node.addDependency(cluster);
  
      // Output the public URL
      new CfnOutput(this, 'ServiceUrl', {
        key: 'ServiceUrl',
        value: cdk.Fn.join('', ['https://', expressService.getAtt('Endpoint').toString()]),
        description: 'Public URL for the UCP MCP service (SSE endpoint: /sse)',
      });
  
      // Output the service ARN
      new CfnOutput(this, 'ServiceArn', {
        key: 'ServiceArn',
        value: expressService.ref,
        description: 'ARN of the Express Gateway Service',
      });
  }
}
