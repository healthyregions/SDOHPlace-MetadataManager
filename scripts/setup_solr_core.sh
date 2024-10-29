#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

sudo su - solr -c "/opt/solr/bin/solr create -c $1 -n data_driven_schema_configs"

sudo mv /var/solr/data/$1/conf /var/solr/data/$1/conf-backup
sudo cp $THIS_DIR/../solr/conf /var/solr/data/$1/ -r

sudo sed -i -e "s/{{SOLR_CORE}}/$1/g" /var/solr/data/$1/conf/solrconfig.xml

sudo service solr restart
