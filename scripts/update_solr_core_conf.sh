#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

sudo mv /var/solr/data/$1/conf /var/solr/data/$1/conf-backup-$(date +"%Y%m%d%H%M")
sudo cp $THIS_DIR/../solr/conf /var/solr/data/$1/ -r

sudo service solr restart

