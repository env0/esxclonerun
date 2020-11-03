terraform {
  required_version  = "=0.12.3"
}

resource "random_id" "id" {
  byte_length = 8
}

data "local_file" "ip" {
  filename = "ip.txt"
}

output "ip" {
  value = data.local_file.ip.content
}
