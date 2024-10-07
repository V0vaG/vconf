#!/bin/bash

b_num=$1

pod_num=$2

sed -i "s/b_num/$b_num/g" ./run.sh

sed -i "s/pod_num/$pod_num/g" ./run.sh

cat ./run.sh

