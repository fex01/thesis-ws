#tfsec:ignore:aws-ec2-require-vpc-flow-logs-for-all-vpcs
module "vpc" {
  source  = "registry.terraform.io/terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  cidr                 = var.cidr_block
  azs                  = data.aws_availability_zones.avzs.names
  enable_dns_hostnames = true

  private_subnets      = [for i in range(var.private_subnets_num) : cidrsubnet(var.cidr_block, 8, i)]
  private_subnet_names = [for i in range(var.private_subnets_num) : "private-subnet-${i}"]
  private_subnet_tags = {
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "owned"
  }

  database_subnets           = [for i in range(var.db_subnets_num) : cidrsubnet(var.cidr_block, 8, var.private_subnets_num + i)]
  database_subnet_names      = [for i in range(var.db_subnets_num) : "db-subnet-${i}"]
  database_subnet_group_name = "rds-db"

  manage_default_security_group  = true
  default_security_group_egress  = []
  default_security_group_ingress = []
  default_security_group_name    = "${var.vpc_name}-default-sg"
  // regula e tfsec beccano un falso positivo riguradante il flowlog durante lo scan 


  map_public_ip_on_launch = false

  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true

  flow_log_cloudwatch_log_group_name_prefix = "/aws/${var.vpc_name}-logz/"
  flow_log_cloudwatch_log_group_name_suffix = "test"
  flow_log_cloudwatch_log_group_kms_key_id  = aws_kms_key.vpc_key.arn

  vpc_tags = {
    Name                                            = var.vpc_name
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "owned"
  }

  tags = {
    LAB   = "tesi_mattia"
    infra = "terraform"
  }
}

resource "aws_kms_key" "vpc_key" {
  enable_key_rotation     = true
  deletion_window_in_days = 7
  policy                  = data.aws_iam_policy_document.cloudwatch.json
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_iam_policy_document" "cloudwatch" {
  policy_id = "key-policy-cloudwatch"
  statement {
    sid = "Enable IAM User Permissions"
    actions = [
      "kms:*",
    ]
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        format(
          "arn:%s:iam::%s:root",
          data.aws_partition.current.partition,
          data.aws_caller_identity.current.account_id
        )
      ]
    }
    resources = ["*"]
  }
  statement {
    sid = "AllowCloudWatchLogs"
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = [
        format(
          "logs.%s.amazonaws.com",
          data.aws_region.current.name
        )
      ]
    }
    resources = ["*"]
  }
}

module "vpc_vpc-endpoints" {
  source  = "registry.terraform.io/terraform-aws-modules/vpc/aws//modules/vpc-endpoints"
  version = "5.1.2"

  vpc_id             = module.vpc.vpc_id
  security_group_ids = [aws_security_group.endpoints.id]
  subnet_ids         = module.vpc.private_subnets

  endpoints = {
    s3 = {
      service         = "s3"
      route_table_ids = module.vpc.private_route_table_ids
      service_type    = "Gateway"
      tags            = { Name = "s3" }
    },
    ec2 = {
      service             = "ec2"
      private_dns_enabled = true
      tags                = { Name = "ec2" }
    },
    sts = {
      service             = "sts"
      private_dns_enabled = true
      tags                = { Name = "sts" }
    },
    ecr_api = {
      service             = "ecr.api"
      private_dns_enabled = true
      tags                = { Name = "ecr_api" }
    },
    ecr_dkr = {
      service             = "ecr.dkr"
      private_dns_enabled = true
      tags                = { Name = "ecr_dkr" }
    },
    ssmmessages = {
      service             = "ssmmessages"
      private_dns_enabled = true
      tags                = { Name = "ssmmessages" }
    },
    ec2messages = {
      service             = "ec2messages"
      private_dns_enabled = true
      tags                = { Name = "ec2messages" }
    },
    ssm = {
      service             = "ssm"
      private_dns_enabled = true
      tags                = { Name = "ssm" }
    },
    cloudwatch = {
      service             = "logs"
      private_dns_enabled = true
      tags                = { Name = "logs" }
    }
  }

  tags = {
    LAB   = "tesi_mattia"
    infra = "terraform"
  }
}

resource "aws_security_group" "endpoints" {
  name        = "endpoints-ingress"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for interface endpoints"

  tags = {
    Name  = "endpoints-ingress"
    LAB   = "tesi_mattia"
    infra = "terraform"
  }
}

resource "aws_security_group_rule" "endpoint-ingress" {
  description              = "Endpoint ingress rule"
  type                     = "ingress"
  security_group_id        = aws_security_group.endpoints.id
  from_port                = 1025
  to_port                  = 65535
  protocol                 = -1
  source_security_group_id = module.eks.node_security_group_id
}
