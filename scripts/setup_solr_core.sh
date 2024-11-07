#! /usr/bin/bash

set -e # exit if error

if [ -z "$1" ]; then
    echo "Error: Please provide a core name"
    exit 1
fi

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

sudo su - solr -c "/opt/solr/bin/solr create -c $1 -n data_driven_schema_configs"

sudo mv /var/solr/data/$1/conf /var/solr/data/$1/conf-backup
sudo cp $THIS_DIR/../solr/conf /var/solr/data/$1/ -r

sudo sed -i -e "s/{{SOLR_CORE}}/$1/g" /var/solr/data/$1/conf/solrconfig.xml

sudo mkdir -p /var/solr/data/$1/data
sudo touch /var/solr/data/$1/data/server-enabled.txt
sudo chown -R solr:solr /var/solr/data/$1/data

sudo systemctl stop solr
sudo systemctl start solr

echo "Successfully created core $1 and enabled PING"