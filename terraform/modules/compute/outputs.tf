output "automation_lambda_arn" {
  value = aws_lambda_function.automation_placeholder.arn
}

output "automation_lambda_role_arn" {
  value = aws_iam_role.automation_lambda.arn
}
