# fabric-rolling-es-elb
A fabric script that performs a rolling restart of an Elasticsearch Cluster which is behind an Elastic Load Balancer

## Motivation
Sometimes Elasticsearch needs a restart, because of several reasons including bugs.
In some businesses, ES becomes a critical part of the infrastructure, making it a service which can't go down.
ES greatly helps in maintaining a HA cluster due to it's sharding and replication architecture.

Although simple, an uncontrolled restart of the cluster can lead to lose of data and/or downtime.

The recommended method is described in [the Elastic documentation](https://www.elastic.co/guide/en/elasticsearch/guide/current/_rolling_restarts.html).

Although you can find some great tools online (I particularly liked [elasticsearch-manager](https://github.com/boldfield/elasticsearch-manager)), your cluster setup may be more complex and may need additional steps in the rolling restart.

Basically, our script is aware of an ELB in front of the cluster, and only restarts data (settings/data: true) nodes, as you might have master-only nodes that won't require a restart.

Python Fabric was chosen because of ease and speed of development.

## Usage
    fab es_rolling_restart:elb_name=<elb>,es_hostname=<es>,es_port=<9200>

Where
#### elb_name
Name of the ELB in AWS.

#### es_hostname
Hostname or Alias you use for connecting to Elasticsearch. Can definitely be your ELB's DNS Name.

#### es_port
Elasticsearch port, usually 9200.

## Future work
Although this is a working script, some more work is required to make it prettier.

* Improve messaging and logging
* Retries on curl calls
* A ruby implementation :)

## License
This piece is released under MIT License.
