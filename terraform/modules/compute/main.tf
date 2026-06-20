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
  name               = "${var.name_prefix}-automation-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "automation_lambda_logs" {
  role       = aws_iam_role.automation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "automation_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src"
  output_path = "${path.module}/lambda_src.zip"
}

# Placeholder Lambda. Phase 4 (IAM governance) and Phase 5 (evidence collection) replace
# this with real automation logic deployed the same way.
resource "aws_lambda_function" "automation_placeholder" {
  function_name    = "${var.name_prefix}-automation-placeholder"
  role             = aws_iam_role.automation_lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.automation_lambda.output_path
  source_code_hash = data.archive_file.automation_lambda.output_base64sha256
  timeout          = 30

  tags = var.tags
}
