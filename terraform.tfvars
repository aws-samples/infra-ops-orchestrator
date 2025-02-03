// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0



# Sample Values, modify accordingly

knowledge_base_name                 = "bedrock-orchestrator-kb"
enable_access_logging               = true
enable_s3_lifecycle_policies        = true
enable_endpoints                    = true
knowledge_base_model_id             = "amazon.titan-embed-text-v2:0"
app_name                            = "XXXXX"
env_name                            = "XXXXX"
app_region                          = "XXXXX"
agent_model_id                      = "anthropic.claude-3-haiku-20240307-v1:0"
bedrock_agent_invoke_log_bucket     = "XXXXX"
agent_name                          = "bedrock-agent"
agent_alias_name                    = "bedrock-agent-alias"
agent_action_group_name             = "bedrock-agent-ag"
aoss_collection_name                = "aoss-collection"
aoss_collection_type                = "VECTORSEARCH"
agent_instructions                  = <<-EOT
[Instructions text kept as is since it's public documentation]
EOT
agent_description                   = "You are Infra Orchestrator Assistant"
agent_actiongroup_descrption        = "Use the action group to perform Infrastructure Orchestration on AWS Services"
kb_instructions_for_agent           = "I am an AWS Infrastructure Orchestrator Assistant - let me know which AWS service (EC2, S3, or RDS) you'd like to manage and optimize according to AWS Well-Architected Framework."
kms_key_id                          = "XXXXX"
vpc_subnet_ids                      = ["XXXXX", "XXXXX"]
vpc_id                              = "XXXXX"
cidr_blocks_sg                      = ["XXXXX", "XXXXX"]
code_base_zip                       = "XXXXX"
code_base_bucket                    = "XXXXX"
enable_guardrails                   = true
guardrail_name                      = "bedrock-guardrail"
guardrail_blocked_input_messaging   = "This input is not allowed due to content restrictions."
guardrail_blocked_outputs_messaging = "The generated output was blocked due to content restrictions."
guardrail_description               = "A guardrail for Bedrock to ensure safe and appropriate content"
guardrail_content_policy_config = [
  {
    filters_config = [
      {
        input_strength  = "MEDIUM"
        output_strength = "MEDIUM"
        type            = "HATE"
      },
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "VIOLENCE"
      }
    ]
  }
]
guardrail_sensitive_information_policy_config = [
  {
    pii_entities_config = [
      {
        action = "BLOCK"
        type   = "NAME"
      },
      {
        action = "BLOCK"
        type   = "EMAIL"
      }
    ],
    regexes_config = [
      {
        action      = "BLOCK"
        description = "Block Social Security Numbers"
        name        = "SSN_Regex"
        pattern     = "^\\d{3}-\\d{2}-\\d{4}$"
      }
    ]
  }
]
guardrail_topic_policy_config = [
  {
    topics_config = [
      {
        name       = "investment_advice"
        examples   = ["Where should I invest my money?", "What stocks should I buy?"]
        type       = "DENY"
        definition = "Any advice or recommendations regarding financial investments or asset allocation."
      }
    ]
  }
]
guardrail_word_policy_config = [
  {
    managed_word_lists_config = [
      {
        type = "PROFANITY"
      }
    ],
    words_config = [
      {
        text = "badword1"
      },
      {
        text = "badword2"
      }
    ]
  }
]