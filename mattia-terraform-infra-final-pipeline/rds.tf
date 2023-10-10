
resource "aws_db_instance" "rds_db" {
  count                  = 1
  db_name                = "tracking"
  allocated_storage      = 20
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  username               = "mattia"
  password               = var.db_pwd
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  skip_final_snapshot    = true //inserito solo per permettere una destroy immediata
  vpc_security_group_ids = [aws_security_group.db_plane_sg.id]

  backup_retention_period               = 5
  iam_database_authentication_enabled   = true
  storage_encrypted                     = true
  #tfsec:ignore:aws-rds-enable-deletion-protection
  deletion_protection                   = false //inserito solo per permettere una destroy immediata
  performance_insights_enabled          = true
  performance_insights_kms_key_id       = aws_kms_key.rds_performance_insights.arn
  performance_insights_retention_period = 7
  multi_az                              = true
  tags = {
    LAB     = "tesi_mattia"
    infra   = "terraform"
    db_name = "rds_db"
  }

}

resource "aws_kms_key" "rds_performance_insights" {
  enable_key_rotation     = true
  deletion_window_in_days = 7
  policy                  = data.aws_iam_policy_document.insight.json
}

data "aws_iam_policy_document" "insight" {
  policy_id = "key-policy-insight"
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
    sid = "Allow viewing RDS Performance Insights"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        format(
          "arn:aws:iam::%s:user/ma.caracciolo@reply.it",
          data.aws_caller_identity.current.account_id
        )
      ]
    }
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["rds.${data.aws_region.current.name}.amazonaws.com"]
    }
    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:EncryptionContext:aws:pi:service"
      values   = ["rds"]
    }
    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:EncryptionContext:service"
      values   = ["pi"]
    }
  }
}

resource "aws_security_group" "db_plane_sg" {
  name        = "db-plane-sg"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for dbs"

  tags = {
    Name  = "db-plane-sg"
    LAB   = "tesi_mattia"
    infra = "terraform"
  }
}

resource "aws_security_group_rule" "node_ingress" {
  description              = "DB ingress rule"
  type                     = "ingress"
  security_group_id        = aws_security_group.db_plane_sg.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = module.eks.node_security_group_id
}

output "endpoint" {
  value = aws_db_instance.rds_db[0].address
}
