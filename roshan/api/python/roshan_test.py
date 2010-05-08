from roshan import Roshan

roshan = Roshan()

roshan.login('zookeeper', 'doublekill')

nodes = roshan.get_node_list('/sandbox/pass-op')
if nodes is not None:
    for node in nodes:
        if node.get('leaf', False) == False:
            print '+',
        print node['text']

roshan.add_node('/sandbox/pass-op/clyfish')
roshan.update_node('/sandbox/pass-op/clyfish', data='I am clyfish')