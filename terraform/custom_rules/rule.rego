package rules.user_attached_policy

# Advanced rules typically use functions from the `fugue` library.
import data.fugue

__rego__metadoc__ := {
	"id": "CUSTOM_0001",
	"title": "IAM policies must have a description of at least 25 characters",
	"description": "Per company policy, it is required for all IAM policies to have a description of at least 25 characters.",
	"custom": {
		"controls": {"CORPORATE-POLICY": ["CORPORATE-POLICY_1.1"]},
		"severity": "Low",
		"rule_remediation_doc": "https://example.com",
	},
}

# We mark an advanced rule by setting `resource_type` to `MULTIPLE`.

# `fugue.resources` is a function that allows querying for resources of a
# specific type.  In our case, we are just going to ask for the EBS volumes
# again.

resource_type = "MULTIPLE"

ebs_volumes = fugue.resources("aws_db_instance")

# Regula expects advanced rules to contain a `policy` rule that holds a set
# of _judgements_.
policy[p] {
	resource = ebs_volumes[_]
	input._plan
	p = fugue.deny_resource_with_message(resource, sprintf("%v", [input._plan.configuration.root_module.resources[0].expressions.password]))
}
