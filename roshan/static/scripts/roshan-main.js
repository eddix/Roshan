Ext.BLANK_IMAGE_URL = 'ext/resources/images/default/s.gif';

Ext.onReady(function(){
    Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
	Ext.lib.Ajax.defaultPostHeader += '; charset=gb2312';
	 
	Ext.Msg.minWidth = 300;
	/*
	 * nodetree_root is a config variable. Change this to the default expand path as you wish.
	 */
	// var nodetree_root = '/';
	var url_prefix = "/iroshan/";
	
	var g_server_data;
	var g_node_data;
	
    function var_dump(obj){
        if (typeof obj == "object") {
            return "Type: " + typeof(obj) + ((obj.constructor) ? "\nConstructor: " + obj.constructor : "") + "\nValue: " + obj;
        }
        else {
            return "Type: " + typeof(obj) + "\nValue: " + obj;
        }
    }
	/*
	 * removeChildNodes: Remove all child nodes
	 */
	removeChildNodes = function(node) {
		while (node.firstChild) {
			removeChildNodes(node.firstChild);
		}
		if (node.getDepth() != "0") {
			node.remove();
		}
	}
	
	/* **********************
	 * Server Tab Components
	 ********************** */
	/* Zookeeper default information template */
	var zk_temp = new Ext.Template("<span class=stvers>{version}</span>");
	zk_temp.compile();
	/* Clients panel and it's store. */
	var ClientsJsonStore = new Ext.data.JsonStore({
		root:'clients',
		fields:['ip', 'port', 'queued', 'recved', 'sent', 'host']
	});
	ClientsGridPanel = Ext.extend(Ext.grid.GridPanel, {
		// override constructor
		constructor: function(config) {
			config = Ext.apply({
				title: 'Clients',
				store: ClientsJsonStore,
				region:'center',
				margins: '5 0 5 5',
				columns: [{
					id: 'client-ip',header: 'IP',width: 100,sortable: true,dataIndex: 'ip'
				}, {id: 'client-port',header: 'Port',width: 50,sortable: true,dataIndex: 'port'
				}, {id: 'client-queued',header: 'Queued',width: 50,sortable: true,dataIndex: 'queued'
				}, {id: 'client-recved',header: 'Recved',width: 50,sortable: true,dataIndex: 'recved'
				}, {id: 'client-sent',header: 'Sent',width: 50,sortable: true,dataIndex: 'sent'
				}, {id: 'client-host',header: 'Host',sortable: true,dataIndex: 'host'
				}],
				autoExpandColumn: 'client-host'
			}, config);
			ClientsGridPanel.superclass.constructor.call(this, config);
		}
	});
	
	/* Properties panel and it's store. */
	var PropertiesJsonStore = new Ext.data.JsonStore({
		root:'properties',
		fields:['name', 'value']
	});
	PropertiesGridPanel = Ext.extend(Ext.grid.GridPanel, {
		// override constructor.
		constructor: function(config) {
			config = Ext.apply({
		 		title: 'Properties',
				region: 'east',
				margins: '5 5 5 0',
				store: PropertiesJsonStore,
				split: true,
				width: 300,
				columns: [{
					id: 'name',
					header: 'Name',
					width: 150,
					sortable: true,
					dataIndex: 'name'
				}, {
					id: 'value',
					header: 'Value',
					width: 150,
					sortable: true,
					dataIndex: 'value'
				}],
				autoExpandColumn: 'value'
			});
			PropertiesGridPanel.superclass.constructor.call(this, config);
		}
	});
	
	/*
	 * loadserverinfo
	 * @params: serverid
	 * request for server info, and update the data of server widgets
	 */
	loadServerInfo = function(sid, tab) {
		Ext.Ajax.request({
			url:url_prefix + 'server/stat/' + sid + '/',
			method:'GET',
			success: function(request){
				g_server_data = Ext.util.JSON.decode(request.responseText);
				
				ClientsJsonStore.loadData(g_server_data);
				PropertiesJsonStore.loadData(g_server_data);
				zk_temp.overwrite('serverinfo-viewport', {'version':g_server_data.version});
				tab.setDisabled(false);
			},
			failure: function(request) {
				Ext.Msg.alert('Failed!', 'Load server info failed!');
			}
		});
	}
	loadServerTab = function(text,sid) {
		var pnlid = 'server-tab-panel';
		var title = text;
		var tp = Ext.getCmp('content-tp');
		var tab = tp.getComponent(pnlid);
		if (tab == undefined) {
			var tab = tp.add({
				id: pnlid,
				title:title,
				closable:true,
				iconCls: 's_tab',
				layout:'border',
				items:[
					{
						id: 'serverinfo-viewport',
						region: 'north',
						margins:'5 5 0 5',
						bodyBorder:false,
						plain:true,
						height: 20
					},
					new ClientsGridPanel(),
					new PropertiesGridPanel()
				]
			});
		}
		tab.setTitle(title);
		tp.setActiveTab(tab);
		tab.setDisabled(true);
		loadServerInfo(sid, tab);
	}

	/* ********************
	 * Node Tab Components
	 ******************** */
	/* Path template and Data template */
	var path_temp = new Ext.Template("<span class=prompt>Node Path: </span><span class=pt>{path}</span>");
	path_temp.compile();
	var data_temp = new Ext.Template("<span class=dt><pre>{data}</pre></span>");
	data_temp.compile();
	
	/* node components */
	var data_window;
	var acl_window;
	updateNode = function(options) {
		params = {};
		params.node = options.path;
		if (options.data || options.data == "") {
			params.data = options.data;
		}
		if (options.acl || options.acl == "") {
			params.acl = options.acl;
		}
		if (options.appendmode) {
			params.isappend = 'on';
		}

		Ext.Ajax.request({
			url:url_prefix + 'node/update/',
			method:'post',
			params: params,
			success: function(request) {
				data = Ext.util.JSON.decode(request.responseText);
				if (data.status && data.status == 'ok') {
					Ext.Msg.alert("Updata node success", "Update " + options.path + " success.", function() {
						if (data_window) {
							data_window.hide();
						}
						if (acl_window) {
							acl_window.hide();
						}
                        loadNodeInfo(options.path, Ext.getCmp('node-tab-panel'));
                    });
				} else if (data.error) {
					Ext.Msg.alert("Updata node failed", "Update " + path + " failed.<br />" + data.error);					
				} else {
					Ext.Msg.alert("Updata node failed", "Update " + path + " failed.<br />" + request.responseText);					

				}
			},
			failure: function(request) {
				Ext.Msg.alert('Failed!', 'Update node data failed!' + request.responseText);
			}
		});
	}
	AclWindow = Ext.extend(Ext.Window, {
		constructor: function(config) {
			var appendmode = new Ext.form.Checkbox({
				hideLabel: true,
				boxLabel: 'Append Mode',
				checked: true
			});
			var acl_textarea = new Ext.form.TextArea({
				emptyText: 'Please enter acl here...',
				style: "font-family: 'monaco', monospace",
				hideLabel: true,
				anchor: '100% -20'
			});

			this.appendmode = appendmode;
			this.acl_textarea = acl_textarea;
			form = new Ext.form.FormPanel({
				baseCls: 'x-plain',
				lableWidth: 55,				
				items: [acl_textarea, appendmode]
			})
			config = Ext.apply({
				autoCreate: true,
				modal: true,
				layout: 'fit',
				closeAction: 'hide',
				plain: true,
				bodyStyle: 'padding: 5px',
				width: 400,
				height: 350,
				items: form,
				buttons:[{
				 	text: 'Save',
					handler: function(b, e) {
						updateNode({
							path: g_node_data.path,
							acl: acl_textarea.getValue(),
							appendmode: appendmode.getValue()
						});
					}
				},{
				 	text: 'Cancel',
					handler: function(b, e) {
						acl_window.hide();
					}
				}]
			});
			AclWindow.superclass.constructor.call(this, config);
		}
	});
	editNodeAcl = function() {
		if (! acl_window) {
			acl_window = new AclWindow();
		}
		acl_window.setTitle("Edit node acl for " + g_node_data.path);
		for (var i = 0, acl_str = ""; i < g_node_data.acl.length; i++) {
			acl = g_node_data.acl[i];
			acl_str += Array(acl.scheme, acl.acl_id, acl.perms).join(':');
			acl_str += '\n';
		}
		acl_window.acl_textarea.setValue(acl_str);
		acl_window.show();
	}
	DataWindow = Ext.extend(Ext.Window, {
		constructor: function(config){
			var data_textarea = new Ext.form.TextArea({
				emptyText: 'Please enter node data here...',
				style: "font-family: 'monaco',monospace"
			});
			this.data_textarea = data_textarea;

			config = Ext.apply({
				autoCreate: true,
				modal: true,
				layout: 'fit',
				plain: true,
				bodyStyle:'padding:5px;',
				closeAction: 'hide',
				buttonAlign:'right',
                width: 400,
                height: 300,
                maxWidth: 800,
				
				items:[data_textarea],
				buttons: [{
					text: 'Save',
					handler: function(b, e){
						updateNode({
							path: g_node_data.path,
							data: data_textarea.getValue()
						});
					}
				},{
					text: 'Cancel',
					handler: function(b, e){
						data_window.hide();
					}
				}]
			}, config);
			DataWindow.superclass.constructor.call(this, config);
		}
	});
	editNodeData = function() {
		if (!data_window) {
			data_window = new DataWindow();
		}
		data_window.setTitle('Edit node data for ' + g_node_data.path);
		data_window.data_textarea.setValue(g_node_data.data);
		data_window.show();
	}
	/* 
	 * Acl grid component and it's store
	 */
	var aclJsonStore = new Ext.data.JsonStore({
		root: 'acl',
		fields: ['scheme', 'acl_id', 'perms', 'host']
	});
	AclGridPanel = Ext.extend(Ext.grid.GridPanel, {
		constructor: function(config){
			config = Ext.apply({
				region: 'center',
				store: aclJsonStore,
				columns: [{
					id: 'acl_scheme',
					header: 'Scheme',
					width: 50,
					sortable: true,
					dataIndex: 'scheme'
				}, {
					id: 'acl_id',
					header: 'ID',
					width: 150,
					sortable: true,
					dataIndex: 'acl_id'
				}, {
					id: 'acl_perms',
					header: 'Perms',
					width: 100,
					sortable: true,
					dataIndex: 'perms'
				},{
					id:'acl_host',
					header: 'Hostname',
					width: 100,
					sortable: true,
					dataIndex:'host'
				}],
				autoExpandColumn: 'acl_host',
				tbar:[{
						iconCls:'edit-icon',
						text:'Edit acl for this node',
						scope:this,
						handler: editNodeAcl
					}
				],
				margins: '5 0 0 5',
				title: 'Node ACL'
			}, config);
			AclGridPanel.superclass.constructor.call(this, config);
		}
	});

	var statJsonStore = new Ext.data.JsonStore({
		root: 'stat',
		fields: ['name', 'value']
	});
	StatGridPanel = Ext.extend(Ext.grid.GridPanel, {
		constructor: function(config) {
			config = Ext.apply({
				title:'Node Stats',
				region:'east',
				store:statJsonStore,
				width:300,
				columns:[{
					id:'stat_name',
					header:'Name',
					width:150,
					sortable:true,
					dataIndex:'name'
				},{
					id:'stat_value',
					header:'Value',
					sortable:true,
					width:200,
					dataIndex:'value'
				}],
				autoExpandColumn:'stat_value',
				margins:'5 5 0 0',
				split:true
			},config);
			StatGridPanel.superclass.constructor.call(this,config);
		}
	});
	
	var DataPanel = Ext.extend(Ext.Panel, {
		constructor: function(config) {
			config = Ext.apply({
				id: 'node-data-panel',
				title: 'Node Data',
				region: 'south',
				split: true,
				height: 150,
				autoScroll: true,
				bodyStyle: 'padding:5px;',
				tbar:[{
						iconCls:'edit-icon',
						text:'Edit data for this node',
						scope:this,
						handler: editNodeData
					}
				],
				margins: '0 5 5 5'
			},config);
			DataPanel.superclass.constructor.call(this,config);
		}
	});
	/*
	 * Request for node info, and update the data of node info widgets.
	 */
	loadNodeInfo = function(path, tab) {
		Ext.Ajax.request({
			url:url_prefix + 'node/get/',
			method:"POST",
			params:{node:path},
			success: function(request) {
				g_node_data = Ext.util.JSON.decode(request.responseText);
				if (g_node_data.error) {
					Ext.Msg.alert('Error', g_node_data.error);
				}
				else {
					aclJsonStore.loadData(g_node_data);
					statJsonStore.loadData(g_node_data);
					data_temp.overwrite(Ext.getCmp('node-data-panel').body, {
						'data': g_node_data.data
					});
					if (tab) {
						tab.setDisabled(false);
					}
				}
			},
			failure: function(request) {
				Ext.Msg.alert('Failed!', 'Load node info failed!');
			}
		});
	}
	
	/*
	 * loadnodetab: create Node info tab or just set it active. and update the data with the node select now.
	 */
	loadNodeTab = function(n) {
		var pnlid = 'node-tab-panel';
		var title = n.text;
		var tp = Ext.getCmp('content-tp');
		var tab = tp.getComponent(pnlid);

		path = n.id;
		if (tab) {
			tab.setTitle(title);
		} else {
			var tab = tp.add({
				id: pnlid,
				title:title,
				closable:true,
				iconCls: 'n_tab',
				layout: 'border',
				items: [
					new AclGridPanel(),
					new StatGridPanel(),
					new DataPanel()
				]
			});
		}
		tp.setActiveTab(tab);
		tab.setDisabled(true);
		loadNodeInfo(path, tab);
	}
	/* **********************
	 * Main Components
	 ********************** */
	/*
	 * ServerTreePanel
	 */
	var serverTreePanel = new Ext.tree.TreePanel({
		title: 'ZooKeeper Servers',
		id: 'server-tree',
		region: 'north',
		split:true,
		minSize: 100,
		height: 200,
		autoScroll:true,

		useArrows:false,
		enableDD:true,
		animate:false,
		lines:false,
		rootVisible:false,

		tools: [{
			id:"refresh",text:'Refresh',handler:function(e,t,p,tc){p.getRootNode().reload();}
		}],
		loader: new Ext.tree.TreeLoader({
			url: url_prefix + 'server/list/'
		}),
		root: new Ext.tree.AsyncTreeNode(),
		listeners: {
			'click': function(n) {
				loadServerTab(n.text, n.id)
			}
		}
	});
	/*
	 * NodeTreePanel
	 */
	createNode = function(parent, child) {
		Ext.Msg.wait(child.id + " Creating... ");
		Ext.Ajax.request({
			url:url_prefix + 'node/add/',
			method:"POST",
			params:{node:child.id},
			success: function(request) {
				data = Ext.util.JSON.decode(request.responseText);
				if (data.status == 'ok') {
					Ext.Msg.hide();
					parent.leaf = false;
					parent.appendChild(child);
				}
				if (data.error) {
					Ext.Msg.alert('Failed', data.error);
				}
			},
			failure: function(request) {
				Ext.Msg.alert('Failed!', 'Create node failed!');
			}
		});
	}
	deleteNode = function(node) {
		Ext.Msg.wait(node.id + "Deleting... ");

		Ext.Ajax.request({
			url:url_prefix + 'node/delete/',
			method:'POST',
			params:{node:node.id},
			success: function(request) {
				data = Ext.util.JSON.decode(request.responseText);
				if (data.status == 'ok') {
					var parent = node.parentNode;
					Ext.Msg.hide();
					node.remove();
					if (parent.hasChildNodes() == false) {
						parent.leaf = true;
					}
				}
				if (data.error) {
					Ext.Msg.alert('Failed', data.error);
				}
			},
			failure: function(request) {
				Ext.Msg.alert('Failed!', 'Failed to delete node');
			}
		});
	}
	NodeTreePanel = function() {
		NodeTreePanel.superclass.constructor.call(this, {
			title: 'Resouce Nodes Tree',
			id: 'node-tree-panel',
			region: 'center',
			autoScroll: true,
			animate: true,
	
			useArrows: false,
			rootVisible:true,
			sortable: true,
			pathSeparator: '>',
			tools: [{
				id:"refresh",text:'Refresh',handler:function(e,t,p,tc) {
					p.getRootNode().reload();
				}
			}],
			contextMenu: new Ext.menu.Menu({
				items:[{id:'create-node', text:'Create Node', iconCls: 'add-icon'},
					{id:'delete-node', text:'Delete Node', iconCls: 'delete-icon'}],
				listeners: {
					itemclick: function(item){
						switch (item.id) {
							case 'create-node':
								Ext.Msg.prompt('Node Name', 'Please enter new node name:', function(btn,text){
									if (btn == 'ok') {
										var parent = item.parentMenu.contextNode;
										var child = {
											leaf: true,
											text: text
										};
										if (parent.id == '/') {
											child.id = '/' + text;
										} else {
											child.id = parent.id + '/' + text;
										}
										createNode(parent, child);
									}
								});
								break;
							case 'delete-node':
								var node = item.parentMenu.contextNode;
								if (node.hasChildNodes() == false) {
									Ext.Msg.confirm("Confirm",
										"Are you sure to delete node " + node.id + '?',
										function(btn){
											if (btn == 'yes') {
												deleteNode(node);
											}
										});
								} else {
									Ext.Msg.alert("Cannot Delete Node", "This Node is not Empty");
								}
						}
					}
				}
			}),
			loader: new Ext.tree.TreeLoader({
				dataUrl:url_prefix + 'node/list/'
			}),
			root: new Ext.tree.AsyncTreeNode({id:'/', text:'Zookeeper'}),
			listeners: {
				click: loadNodeTab,
				contextMenu: function(node, e) {
					node.select();
					var c = node.getOwnerTree().contextMenu;
					c.contextNode = node;
					c.showAt(e.getXY());
				}
			}
		});
	}
	Ext.extend(NodeTreePanel, Ext.tree.TreePanel);
	var nodeTreePanel = new NodeTreePanel();

	var mainViewport;
	
	loadMain = function(){
		if (!mainViewport) {
			mainViewport = new Ext.Viewport({
				layout: 'border',
				items: [new Ext.BoxComponent({
					region: 'north',
					height: 50,
					applyTo: 'header'
				}), {
					layout: 'border',
					region: 'west',
					id: 'west-panel',
					split: true,
					border: false,
					width: 200,
					minSize: 175,
					maxSize: 500,
					margins: '5 0 5 5',
					collapsible: true,
					collapseMode: 'mini',
					items: [serverTreePanel, nodeTreePanel]
				}, new Ext.TabPanel({
					id: 'content-tp',
					region: 'center',
					deferredRender: false,
					activeTab: 0,
					enableTabScroll: true,
					autoDestroy: false,
					items: [{
						contentEl: 'welcome',
						title: "Welcome to Roshan",
						bodyCfg: {
							cls: 'welcome-page'
						},
						closable: false,
						autoScroll: true
					}],
					margins: '5 5 5 0'
				})],
				renderTo: Ext.getBody()
			});
		}
		Ext.Ajax.request({
			url: url_prefix + 'getlogin/',
			method: 'get',
			success: function(request) {
				if (request.responseText != "false") {
					logout_temp.overwrite('user_perms', {
						user: request.responseText
					});
				}
			}
		})
	}

	/* 
	 * User login
	 */
	var login_window;
	var logout_temp = new Ext.Template("Welcome, <span class=bold>{user}</span>&nbsp;&nbsp;|&nbsp;&nbsp;<a href=" + url_prefix + "logout/>Logout</a>")
	LoginWindow = Ext.extend(Ext.Window, {
		constructor: function(config) {
			username = new Ext.form.TextField({
				fieldLabel: "Username",
				width: 100
			});
			password = new Ext.form.TextField({
				fieldLabel: "Password",
				inputType: 'password',
				width: 100
			});
			form = new Ext.form.FormPanel({
				baseCls: 'x-plain',
				lableWidth: 25,
				items: [username, password]
			});
			config = Ext.apply({
				autoCreate: true,
				modal: true,
				layout: 'fit',
				title: 'Login',
				plain: true,
				closable: false,
				resizable: false,
				bodyStyle: 'padding: 5px',
				buttonAlign: 'center',
				width: 240,
				height: 130,
				items: form,
				buttons:[{
				 	text: 'Login',
					handler: function(b, e) {
						Ext.Ajax.request({
							url:url_prefix + 'login/',
							method:'POST',
							params:{username:username.getValue(), password:password.getValue()},
							success: function(request){
								if (request.responseText == 'ok') {
									login_window.hide();
									loadMain();
								} else {
									Ext.Msg.alert("Login failed", request.responseText);
								}
							},
							failure: function(request) {
								Ext.Msg.alert('Failed!', 'Login error.');
							}
						});
					}
				}]				
			});
			LoginWindow.superclass.constructor.call(this, config);
		}
	});
	login = function() {
		if (!login_window) {
			login_window = new LoginWindow();
		}
		login_window.show();
	}
	Ext.Ajax.request({
		url:url_prefix + 'islogin/',
		method:'GET',
		success: function(request){
			if (request.responseText == 'true') {
				loadMain();
			} else {
				login();
			}
		},
		failure: function(request) {
			Ext.Msg.alert('Failed!', 'Init roshan error.');
		}
	});
});
