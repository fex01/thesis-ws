#tfsec:ignore:aws-ec2-no-public-egress-sgr
#tfsec:ignore:aws-eks-no-public-cluster-access
#tfsec:ignore:aws-eks-no-public-cluster-access-to-cidr
module "eks" {
  source  = "registry.terraform.io/terraform-aws-modules/eks/aws"
  version = "19.17.2"

  cluster_name = var.eks_cluster_name

  iam_role_name = "${var.eks_cluster_name}-cluster"
  iam_role_tags = {
    Name = "${var.eks_cluster_name}-cluster"
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    private-nodes = {
      create         = true
      capacity_type  = "ON_DEMAND"
      instance_types = ["t3a.medium"]
      desired_size   = 1
      max_size       = 2
      min_size       = 1
      iam_role_additional_policies = {
        "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore" = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      }
    }
  }

  cluster_endpoint_public_access = true
  enable_irsa                    = false
  cluster_enabled_log_types      = ["api", "authenticator", "audit", "scheduler", "controllerManager"]


  node_security_group_additional_rules = {
    egress_all = {
      description = "Allow egress only inside the vpc and to other AWS IPs"
      protocol    = "-1"
      from_port   = 0
      to_port     = 65535
      type        = "egress"
      cidr_blocks = [module.vpc.vpc_cidr_block, "16.12.18.0/23", "16.12.20.0/24", "3.5.224.0/22", "52.95.154.0/23", "52.95.156.0/24"]
    }
    # FORSE NON HAI AGGIUNTO LA VIOLATION -> "CRITICAL Security group rule allows egress to multiple public internet addresses"
  }
  create_cloudwatch_log_group = false


  cluster_addons = {
    "vpc-cni" = {
      addon_version     = "v1.12.5-eksbuild.2"
      resolve_conflicts = "OVERWRITE"
    }
  }

  tags = {
    LAB   = "tesi_mattia"
    infra = "terraform"
  }
}


