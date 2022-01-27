#!/bin/bash

sed -i -e 's/terraform fmt -diff -check/terraform fmt/' hooks/terraform-fmt.sh
