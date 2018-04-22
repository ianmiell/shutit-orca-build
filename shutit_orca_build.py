# Generated by shutit skeleton
import random
import datetime
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class shutit_orca_build(ShutItModule):


	def build(self, shutit):
		shutit.run_script('''#!/bin/bash
MODULE_NAME=shutit_orca_build
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
XARGS_FLAG='--no-run-if-empty'
if echo '' | xargs --no-run-if-empty
then
	XARGS_FLAG=''
fi
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep shutit_orca_build | awk '{print $1}'| xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -n1 virsh destroy || true
fi''')
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		shutit.build['module_name'] = 'shutit_orca_build_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + shutit.build['module_name']
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		shutit.send('command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|
config.landrush.enabled = true
config.vm.provider "virtualbox" do |vb|
vb.gui = ''' + gui + '''
vb.memory = "''' + memory + '''"
end

config.vm.define "orca1" do |orca1|
orca1.vm.box = ''' + '"' + vagrant_image + '"' + '''
orca1.vm.hostname = "orca1.vagrant.test"
config.vm.provider :virtualbox do |vb|
vb.name = "shutit_orca_build_1"
end
end
end''')

		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'orca1':{'fqdn':'orca1.vagrant.test'}})

		try:
			pw = file('secret').read().strip()
		except IOError:
			pw = ''
		if pw == '':
			shutit.log("""You can get round this manual step by creating a 'secret' with your password: 'touch secret && chmod 700 secret'""",level=logging.CRITICAL)
			pw = shutit.get_env_pass()
			import time
			time.sleep(10)

		# Set up the sessions
		shutit_sessions = {}
		for machine in sorted(machines.keys()):
			shutit_sessions.update({machine:shutit.create_session('bash')})
		# Set up and validate landrush
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.send('cd ' + shutit.build['this_vagrant_run_dir'])
			# Remove any existing landrush entry.
			shutit_session.send('vagrant landrush rm ' + machines[machine]['fqdn'])
			# Needs to be done serially for stability reasons.
			try:
				shutit_session.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + machine_name,{'assword for':pw,'assword:':pw})
			except NameError:
				shutit.multisend('vagrant up ' + machine,{'assword for':pw,'assword:':pw},timeout=99999)
			if shutit.send_and_get_output("vagrant status 2> /dev/null | grep -w ^" + machine + " | awk '{print $2}'") != 'running':
				shutit.pause_point("machine: " + machine + " appears not to have come up cleanly")
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})
			# Check that the landrush entry is there.
			shutit_session.send('vagrant landrush ls | grep -w ' + machines[machine]['fqdn'])
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')
			# Correct /etc/hosts
			shutit_session.send(r'''cat <(echo -n $(ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/') $(hostname)) <(cat /etc/hosts | grep -v $(hostname -s)) > /tmp/hosts && mv -f /tmp/hosts /etc/hosts''')
			# Correct any broken ip addresses.
			if shutit_session.send_and_get_output('''vagrant landrush ls | grep ''' + machine + ''' | grep 10.0.2.15 | wc -l''') != '0':
				shutit_session.log('A 10.0.2.15 landrush ip was detected for machine: ' + machine + ', correcting.',level=logging.WARNING)
				# This beaut gets all the eth0 addresses from the machine and picks the first one that it not 10.0.2.15.
				while True:
					ipaddr = shutit_session.send_and_get_output(r'''ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/' ''')
					if ipaddr[0] not in ('1','2','3','4','5','6','7','8','9'):
						time.sleep(10)
					else:
						break
				# Send this on the host (shutit, not shutit_session)
				shutit.send('vagrant landrush set ' + machines[machine]['fqdn'] + ' ' + ipaddr)
		# Gather landrush info
		for machine in sorted(machines.keys()):
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})



		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.run_script(r'''#!/bin/sh
# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh
fallocate -l ''' + shutit.cfg[self.module_id]['swapsize'] + r''' /swapfile
ls -lh /swapfile
chown root:root /swapfile
chmod 0600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
swapon -s
grep -i --color swap /proc/meminfo
echo "
/swapfile noneswapsw0 0" >> /etc/fstab''')
			shutit_session.multisend('adduser person',{'Enter new UNIX password':'person','Retype new UNIX password:':'person','Full Name':'','Phone':'','Room':'','Other':'','Is the information correct':'Y'})

		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			# Inhibit fastestmirror, which doesn't play nice on this VM for some reason
			shutit_session.send('''yum clean all && sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf''')

			# enable namespaces: 
			shutit_session.send('grubby --args="user_namespace.enable=1" --update-kernel="$(grubby --default-kernel)"')
			shutit_session.send('grubby --args="namespace.unpriv_enable=1" --update-kernel="$(grubby --default-kernel)"')
			shutit_session.send('echo "user.max_user_namespaces=15076" >> /etc/sysctl.conf')

			# reboot and login again
			shutit_session.send('sleep 10 && reboot &')
			shutit_session.logout()
			shutit_session.logout()
			shutit_session.send('sleep 10')
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')
			
			# TODO: only some of these are needed.
			# For python3
			shutit_session.send('yum -q -y install https://centos7.iuscommunity.org/ius-release.rpm')
			shutit_session.send('yum -q -y install python3u make golang git python36u skopeo runc yum-utils device-mapper-persistent-data lvm2')
			# Install the right version of docker such that proot can be built within a container
			shutit_session.send('yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo')
			shutit_session.send('yum install -q -y docker-ce')
			shutit_session.send('systemctl enable docker')
			shutit_session.send('systemctl start docker')

			# Set up GOPATH: TODO: change GOPATH to something saner
			shutit_session.send('mkdir /usr/local/go')
			shutit_session.send('export GOPATH=/usr/local/go')
			# Install runrootless https://github.com/rootless-containers/runrootless
			shutit_session.send('go get github.com/rootless-containers/runrootless')
			shutit_session.send('cp ${GOPATH}/bin/runrootless /usr/local/bin')
			# depends on docker (see above)
			shutit_session.send('${GOPATH}/src/github.com/rootless-containers/runrootless/install-proot.sh')
			shutit_session.send('docker run --rm --name proot -d runrootless-proot sleep infinity')
			shutit_session.send('docker cp proot:/proot /usr/local/bin')
			shutit_session.send('docker rm -f proot')
			# Set up the rootless symlink where orcabuild/umoci expects it.
			shutit_session.login(command='su - person')
			shutit_session.send('mkdir -p /home/person/.runrootless')
			shutit_session.send('ln -s /usr/local/bin/proot /home/person/.runrootless/runrootless-proot')
			shutit_session.logout()

			# TODO: remove docker here?

			# Install https://github.com/openSUSE/umoci
			shutit_session.send('go get -d github.com/openSUSE/umoci || true')
			shutit_session.send('cd ${GOPATH}/src/github.com/openSUSE/umoci')
			shutit_session.send('make install')
			shutit_session.send('cp ${GOPATH}/bin/umoci /usr/local/bin/')

			# Install https://github.com/cyphar/orca-build
			# Install python3
			shutit_session.send('ln -s /usr/bin/python3.6 /usr/bin/python3')
			shutit_session.send('cd')
			shutit_session.send('git clone https://github.com/cyphar/orca-build')
			shutit_session.send('cd orca-build')
			# Hack to use runrootless rather than runc
			shutit_session.send(r'''sed -i 's/\(.*self.runc = "\)runc"/\1runrootless"/' orca-build''')
			shutit_session.send('make install')

			# Log in as unprivileged user and build a container
			shutit_session.login(command='su - person')
			shutit_session.send('mkdir hellohost')
			shutit_session.send('cd hellohost')
			shutit_session.send('''cat > Dockerfile << EOF
FROM centos:7
RUN yum install -y httpd
CMD echo Hello host && sleep infinity
EOF''')

			# --rootless is required as we are not root and are doing a yum install
			shutit_session.send('orca-build --rootless -t final --output /tmp/oci-image $(pwd)')
			shutit_session.send('skopeo copy --format v2s2 oci:/tmp/oci-image:final docker-archive:/home/person/docker-image.tar:badger')
			shutit_session.logout()

			# Back as root, load the image in.
			shutit_session.send('cat /home/person/docker-image.tar | docker load')
			shutit_session.send('docker images')
			shutit_session.send('docker run -d --rm --name badger badger:latest')
			shutit_session.send('docker logs badger')
			shutit_session.send('docker ps')
			shutit_session.pause_point('docker image running')
			shutit_session.send('docker rm -f badger')
		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='centos/7')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'swapsize',default='2G')
		return True


def module():
	return shutit_orca_build(
		'git.shutit_orca_build.shutit_orca_build', 1125038172.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
