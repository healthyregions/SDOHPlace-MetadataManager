#! /usr/bin/bash

sudo su - solr -c "/opt/solr/bin/solr delete -c $1"
