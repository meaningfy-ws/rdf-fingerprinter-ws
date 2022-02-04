set -o allexport; source bash/.env; set +o allexport

wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-3.17.0.tar.gz
tar xzf apache-jena-fuseki-3.17.0.tar.gz
mv apache-jena-fuseki-3.17.0 fuseki
rm apache-jena-fuseki-3.17.0.tar.gz
