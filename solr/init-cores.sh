#!/bin/bash
# Initialize both dev and prod cores for SDOHPlace Metadata Manager

# Start Solr in the background
solr-precreate blacklight-core-dev /solr-configset &

# Wait for Solr to be ready
echo "Waiting for Solr to start..."
sleep 30

# Create the production core
echo "Creating production core..."
solr create_core -c blacklight-core-prod -d /solr-configset

# Keep the container running
wait

