data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "automation_lambda" {
  name               = "${var.name_prefix}-${var.function_name_suffix}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "automation_lambda_logs" {
  role       = aws_iam_role.automation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "automation_lambda_extra" {
  count  = var.extra_policy_json == null ? 0 : 1
  name   = "${var.name_prefix}-${var.function_name_suffix}-extra"
  role   = aws_iam_role.automation_lambda.id
  policy = var.extra_policy_json
}

data "archive_file" "automation_lambda" {
  type        = "zip"
  output_path = "${path.module}/.archives/${var.function_name_suffix}.zip"

  dynamic "source" {
    for_each = fileset(var.source_dir, "**/*.py")
    content {
      content  = file("${var.source_dir}/${source.value}")
      filename = "${var.package_name}/${source.value}"
    }
  }
}

resource "aws_lambda_function" "automation_placeholder" {
  function_name    = "${var.name_prefix}-${var.function_name_suffix}"
  role             = aws_iam_role.automation_lambda.arn
  handler          = var.handler
  runtime          = var.runtime
  filename         = data.archive_file.automation_lambda.output_path
  source_code_hash = data.archive_file.automation_lambda.output_base64sha256
  timeout          = var.timeout

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = var.environment_variables
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_event_rule" "schedule" {
  count               = var.schedule_expression == null ? 0 : 1
  name                = "${var.name_prefix}-${var.function_name_suffix}-schedule"
  schedule_expression = var.schedule_expression
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "schedule" {
  count = var.schedule_expression == null ? 0 : 1
  rule  = aws_cloudwatch_event_rule.schedule[0].name
  arn   = aws_lambda_function.automation_placeholder.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  count         = var.schedule_expression == null ? 0 : 1
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.automation_placeholder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule[0].arn
}
