from fabric.api import *
from elasticsearch import *
import time

env.colorize_errors = True

@task
def es_rolling_restart(elb_name, es_hostname, es_port = 9200):
  print "ELB Name: %s" % elb_name
  print "Elasticsearch Hostname: %s" % es_hostname
  print "Elasticsearch Port: %s" % es_port

  es = Elasticsearch(["http://%s:%s" % (es_hostname, es_port) ])

  nodes = []

  for n in es.nodes.info(flat_settings = 'true').items()[1][1].items():
    if n[1]['settings']['node.data'] == 'true':
      nodes.append({'ip': n[1]['ip'], 'instance_id': n[1]['attributes']['instanceid'], 'data': n[1]['settings']['node.data'], 'master': n[1]['settings']['node.master']})

  print "There are %s nodes in the cluster." % len(nodes)
  for node in nodes:
    print "%s - %s" % (node['instance_id'], node['ip'])

  print "\n\n"

  print "Starting rolling restart with ELB deregistration in 1 minute. Please cancel if not intended.\n\n"
  time.sleep(60)

  i=1
  for node in nodes:
    print "==> Restarting node %s/%s " % (i,len(nodes))
    print "Deregistering node from ELB: %s - %s" % (node['instance_id'], node['ip'])
    local ("aws elb deregister-instances-from-load-balancer --load-balancer-name %s --instances %s" % (elb_name, node['instance_id']))
    time.sleep(10)

    print "Disabling allocation in the cluster."
    local ("curl --connect-timeout 10 --max-time 20 --retry 3 --retry-delay 5 --retry-max-time 120 -XPUT %s:%s/_cluster/settings -d '{\"transient\":{\"cluster.routing.allocation.enable\": \"none\"}}'" % (es_hostname, es_port) )

    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']

    print "Shutting down node: %s - %s" % (node['instance_id'], node['ip'])
    local ("curl --connect-timeout 10 --max-time 20 --retry 3 --retry-delay 5 --retry-max-time 120 -XPOST %s:%s/_cluster/nodes/%s/_shutdown" % (es_hostname, es_port,node['ip']))

    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']

    nodelist = []
    for n in es.nodes.info(flat_settings = 'true').items()[1][1].items():
      nodelist.append(n[1]['ip'])

    print "Waiting for node to leave the cluster "
    while node['ip'] in nodelist:
      print '.'
      time.sleep(5)
      nodelist = []
      for n in es.nodes.info(flat_settings = 'true').items()[1][1].items():
        nodelist.append(n[1]['ip'])
    print " [DONE]"

    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']

    print "Restarting service on the node over ssh: %s - %s" % (node['instance_id'], node['ip'])
    local ("ssh %s sudo /sbin/service elasticsearch restart" % (node['ip']))

    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']

    nodelist = []
    for n in es.nodes.info(flat_settings = 'true').items()[1][1].items():
      nodelist.append(n[1]['ip'])

    print "Waiting for node to join the cluster again "
    while node['ip'] not in nodelist:
      print '.'
      time.sleep(5)
      nodelist = []
      for n in es.nodes.info(flat_settings = 'true').items()[1][1].items():
        nodelist.append(n[1]['ip'])
    print " [DONE]"

    print "Re-Enabling allocation in the cluster."
    local ("curl --connect-timeout 10 --max-time 20 --retry 3 --retry-delay 5 --retry-max-time 120 -XPUT %s:%s/_cluster/settings -d '{\"transient\":{\"cluster.routing.allocation.enable\": \"all\"}}'" % (es_hostname, es_port) )

    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']
    print "Waiting for the cluster to get green "
    es.cluster.health(wait_for_status='green', request_timeout=60)
    print " [DONE]"
    print "Current cluster status: %s" % es.cluster.health(request_timeout=60)['status']

    print "Registering node back into ELB: %s - %s" % (node['instance_id'], node['ip'])
    local ("aws elb register-instances-with-load-balancer --load-balancer-name %s --instances %s" % (elb_name, node['instance_id']))
    print "\n\n"
    time.sleep(5)

    print "Sleeping 15 seconds until the next node."
    time.sleep(15)
    i += 1

  print "\nRolling restart complete."
