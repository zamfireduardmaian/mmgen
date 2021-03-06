#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
opts.py:  MMGen-specific options processing after generic processing by share.Opts
"""
import sys,os

class opt(object): pass

from mmgen.globalvars import g
import mmgen.share.Opts
from mmgen.util import *

def usage(): Die(2,'USAGE: %s %s' % (g.prog_name, usage_txt))

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in group]
		if len(bad) > 1:
			die(1,'Conflicting options: %s' % ', '.join([fmt_opt(b) for b in bad]))

def fmt_opt(o): return '--' + o.replace('_','-')

def _show_hash_presets():
	fs = '  {:<7} {:<6} {:<3}  {}'
	msg('Available parameters for scrypt.hash():')
	msg(fs.format('Preset','N','r','p'))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format("'%s'" % i, *g.hash_presets[i]))
	msg('N = memory usage (power of two), p = iterations (rounds)')

# most, but not all, of these set the corresponding global var
common_opts_data = """
--, --coin=c              Choose coin unit. Default: {cu_dfl}. Options: {cu_all}
--, --color=0|1           Disable or enable color output
--, --force-256-color     Force 256-color output when color is enabled
--, --bitcoin-data-dir=d  Specify Bitcoin data directory location 'd'
--, --data-dir=d          Specify {pnm} data directory location 'd'
--, --no-license          Suppress the GPL license prompt
--, --rpc-host=h          Communicate with bitcoind running on host 'h'
--, --rpc-port=p          Communicate with bitcoind listening on port 'p'
--, --rpc-user=user       Override 'rpcuser' in bitcoin.conf
--, --rpc-password=pass   Override 'rpcpassword' in bitcoin.conf
--, --regtest=0|1         Disable or enable regtest mode
--, --testnet=0|1         Disable or enable testnet
--, --skip-cfg-file       Skip reading the configuration file
--, --version             Print version information and exit
--, --bob                 Switch to user "Bob" in MMGen regtest setup
--, --alice               Switch to user "Alice" in MMGen regtest setup
""".format(
	pnm=g.proj_name,
	cu_dfl=g.coin,
	cu_all=' '.join(g.coins),
	)

def opt_preproc_debug(short_opts,long_opts,skipped_opts,uopts,args):
	d = (
		('Cmdline',            ' '.join(sys.argv)),
		('Short opts',         short_opts),
		('Long opts',          long_opts),
		('Skipped opts',       skipped_opts),
		('User-selected opts', uopts),
		('Cmd args',           args),
	)
	Msg('\n=== opts.py debug ===')
	for e in d: Msg('    {:<20}: {}'.format(*e))

def opt_postproc_debug():
	opt.verbose,opt.quiet = True,None
	a = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) != None]
	b = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) == None]
	Msg('    Opts after processing:')
	for k in a:
		v = getattr(opt,k)
		Msg('        %-18s: %-6s [%s]' % (k,v,type(v).__name__))
	Msg("    Opts set to 'None':")
	Msg('        %s\n' % '\n        '.join(b))
	Msg('    Global vars:')
	for e in [d for d in dir(g) if d[:2] != '__']:
		Msg('        {:<20}: {}'.format(e, getattr(g,e)))
	Msg('\n=== end opts.py debug ===\n')

def opt_postproc_initializations():
	from mmgen.term import set_terminal_vars
	set_terminal_vars()

	# testnet data_dir differs from data_dir_root, so check or create
	from mmgen.util import msg,die,check_or_create_dir
	check_or_create_dir(g.data_dir) # dies on error

	from mmgen.color import init_color
	init_color(enable_color=g.color,num_colors=('auto',256)[bool(g.force_256_color)])

	if g.platform == 'win': start_mscolor()

	g.coin = g.coin.upper() # allow user to use lowercase

def	set_data_dir_root():
	g.data_dir_root = os.path.normpath(os.path.expanduser(opt.data_dir)) if opt.data_dir else \
			os.path.join(g.home_dir,'.'+g.proj_name.lower())

	# mainnet and testnet share cfg file, as with Core
	g.cfg_file = os.path.join(g.data_dir_root,'{}.cfg'.format(g.proj_name.lower()))

def get_data_from_config_file():
	from mmgen.util import msg,die,check_or_create_dir
	check_or_create_dir(g.data_dir_root) # dies on error

	# https://wiki.debian.org/Python:
	#   Debian (Ubuntu) sys.prefix is '/usr' rather than '/usr/local, so add 'local'
	# TODO - test for Windows
	# This must match the configuration in setup.py
	data = u''
	try:
		with open(g.cfg_file,'rb') as f: data = f.read().decode('utf8')
	except:
		cfg_template = os.path.join(*([sys.prefix]
					+ (['share'],['local','share'])[g.platform=='linux']
					+ [g.proj_name.lower(),os.path.basename(g.cfg_file)]))
		try:
			with open(cfg_template,'rb') as f: template_data = f.read()
		except:
			msg("WARNING: configuration template not found at '{}'".format(cfg_template))
		else:
			try:
				with open(g.cfg_file,'wb') as f: f.write(template_data)
				os.chmod(g.cfg_file,0600)
			except:
				die(2,"ERROR: unable to write to datadir '{}'".format(g.data_dir))
	return data

def override_from_cfg_file(cfg_data):
	from mmgen.util import die,strip_comments,set_for_type
	import re
	for n,l in enumerate(cfg_data.splitlines(),1): # DOS-safe
		l = strip_comments(l)
		if l == '': continue
		m = re.match(r'(\w+)\s+(\S+)$',l)
		if not m: die(2,"Parse error in file '{}', line {}".format(g.cfg_file,n))
		name,val = m.groups()
		if name in g.cfg_file_opts:
			setattr(g,name,set_for_type(val,getattr(g,name),name,src=g.cfg_file))
		else:
			die(2,"'{}': unrecognized option in '{}'".format(name,g.cfg_file))

def override_from_env():
	from mmgen.util import set_for_type
	for name in g.env_opts:
		idx,invert_bool = ((6,False),(14,True))[name[:14]=='MMGEN_DISABLE_']
		val = os.getenv(name) # os.getenv() returns None if env var is unset
		if val: # exclude empty string values too
			gname = name[idx:].lower()
			setattr(g,gname,set_for_type(val,getattr(g,gname),name,invert_bool))

def init(opts_f,add_opts=[],opt_filter=None):

	opts_data = opts_f()
	opts_data['long_options'] = common_opts_data

	version_info = """
    {pgnm_uc} version {g.version}
    Part of the {pnm} suite, a Bitcoin cold-storage solution for the command line.
    Copyright (C) {g.Cdates} {g.author} {g.email}
	""".format(pnm=g.proj_name, g=g, pgnm_uc=g.prog_name.upper()).strip()

	uopts,args,short_opts,long_opts,skipped_opts,do_help = \
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter,defer_help=True)

	if g.debug: opt_preproc_debug(short_opts,long_opts,skipped_opts,uopts,args)

	# Save this for usage()
	global usage_txt
	usage_txt = opts_data['usage']

	# Transfer uopts into opt, setting program's opts + required opts to None if not set by user
	for o in tuple([s.rstrip('=') for s in long_opts] + add_opts + skipped_opts) + \
				g.required_opts + g.common_opts:
		setattr(opt,o,uopts[o] if o in uopts else None)

	if opt.version: Die(0,version_info)

	# === Interaction with global vars begins here ===

	# NB: user opt --data-dir is actually g.data_dir_root
	# cfg file is in g.data_dir_root, wallet and other data are in g.data_dir
	# Must set g.data_dir_root and g.cfg_file from cmdline before processing cfg file
	set_data_dir_root()
	if not opt.skip_cfg_file:
		cfg_data = get_data_from_config_file()
		override_from_cfg_file(cfg_data)
	override_from_env()

	# User opt sets global var - do these here, before opt is set from g.global_sets_opt
	for k in g.common_opts:
		val = getattr(opt,k)
		if val != None: setattr(g,k,set_for_type(val,getattr(g,k),'--'+k))

	if g.regtest: g.testnet = True # These are equivalent for now

#	Global vars are now final, including g.testnet, so we can set g.data_dir
	g.data_dir=os.path.normpath(os.path.join(g.data_dir_root,('',g.testnet_name)[g.testnet]))

	# If user opt is set, convert its type based on value in mmgen.globalvars (g)
	# If unset, set it to default value in mmgen.globalvars (g)
	setattr(opt,'set_by_user',[])
	for k in g.global_sets_opt:
		if k in opt.__dict__ and getattr(opt,k) != None:
#			_typeconvert_from_dfl(k)
			setattr(opt,k,set_for_type(getattr(opt,k),getattr(g,k),'--'+k))
			opt.set_by_user.append(k)
		else:
			setattr(opt,k,g.__dict__[k])

	# Check user-set opts without modifying them
	if not check_opts(uopts):
		sys.exit(1)

	if opt.show_hash_presets:
		_show_hash_presets()
		sys.exit(0)

	if opt.verbose: opt.quiet = None

	die_on_incompatible_opts(g.incompatible_opts)

	opt_postproc_initializations()

	if do_help: # print help screen only after global vars are initialized
		opts_data = opts_f()
		opts_data['long_options'] = common_opts_data
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter)

	# We don't need this data anymore
	del mmgen.share.Opts
	del opts_f
	for k in ('prog_name','desc','usage','options','notes'):
		if k in opts_data: del opts_data[k]

	if g.bob or g.alice:
		import regtest as rt
		rt.user(('alice','bob')[g.bob],quiet=True)
		g.testnet = True
		g.rpc_host = 'localhost'
		g.rpc_port = rt.rpc_port
		g.rpc_user = rt.rpc_user
		g.rpc_password = rt.rpc_password
		g.data_dir = os.path.join(g.home_dir,'.'+g.proj_name.lower(),'regtest')

	if g.debug: opt_postproc_debug()

	return args

def check_opts(usr_opts):       # Returns false if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = 'comma' if sep == ',' else 'colon' if sep == ':' else "'%s'" % sep
		try: l = val.split(sep)
		except:
			msg("'%s': invalid %s (not %s-separated list)" % (val,desc,sepword))
			return False

		if len(l) == n: return True
		else:
			msg("'%s': invalid %s (%s %s-separated items required)" %
					(val,desc,n,sepword))
			return False

	def opt_compares(val,op,target,desc,what=''):
		if what: what += ' '
		if not eval('%s %s %s' % (val, op, target)):
			msg('%s: invalid %s (%snot %s %s)' % (val,desc,what,op,target))
			return False
		return True

	def opt_is_int(val,desc):
		try: int(val)
		except:
			msg("'%s': invalid %s (not an integer)" % (val,desc))
			return False
		return True

	def opt_is_tx_fee(val,desc):
		from mmgen.tx import MMGenTX
		ret = MMGenTX().convert_fee_spec(val,224,on_fail='return')
		if ret == False:
			msg("'{}': invalid {} (not a {} amount or satoshis-per-byte specification)".format(
					val,desc,g.coin.upper()))
		elif ret != None and ret > g.max_tx_fee:
			msg("'{}': invalid {} (> max_tx_fee ({} {}))".format(val,desc,g.max_tx_fee,g.coin.upper()))
		else:
			return True
		return False

	def opt_is_in_list(val,lst,desc):
		if val not in lst:
			q,sep = (('',','),("'","','"))[type(lst[0]) == str]
			msg('{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'.format(
					v=val,w=desc,q=q,
					o=sep.join([str(i) for i in sorted(lst)])
				))
			return False
		return True

	def opt_unrecognized(key,val,desc):
		msg("'%s': unrecognized %s for option '%s'"
				% (val,desc,fmt_opt(key)))
		return False

	def opt_display(key,val='',beg='For selected',end=':\n'):
		s = '%s=%s' % (fmt_opt(key),val) if val else fmt_opt(key)
		msg_r("%s option '%s'%s" % (beg,s,end))

	global opt
	for key,val in [(k,getattr(opt,k)) for k in usr_opts]:

		desc = "parameter for '%s' option" % fmt_opt(key)

		from mmgen.util import check_infile,check_outfile,check_outdir
		# Check for file existence and readability
		if key in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			check_infile(val)  # exits on error
			continue

		if key == 'outdir':
			check_outdir(val)  # exits on error
# 		# NEW
		elif key in ('in_fmt','out_fmt'):
			from mmgen.seed import SeedSource,IncogWallet,Brainwallet,IncogWalletHidden
			sstype = SeedSource.fmt_code_to_type(val)
			if not sstype:
				return opt_unrecognized(key,val,'format code')
			if key == 'out_fmt':
				p = 'hidden_incog_output_params'
				if sstype == IncogWalletHidden and not getattr(opt,p):
						die(1,'Hidden incog format output requested. You must supply'
						+ " a file and offset with the '%s' option" % fmt_opt(p))
				if issubclass(sstype,IncogWallet) and opt.old_incog_fmt:
					opt_display(key,val,beg='Selected',end=' ')
					opt_display('old_incog_fmt',beg='conflicts with',end=':\n')
					die(1,'Export to old incog wallet format unsupported')
				elif issubclass(sstype,Brainwallet):
					die(1,'Output to brainwallet format unsupported')
		elif key in ('hidden_incog_input_params','hidden_incog_output_params'):
			a = val.split(',')
			if len(a) < 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			fn,ofs = ','.join(a[:-1]),a[-1] # permit comma in filename
			if not opt_is_int(ofs,desc): return False
			if key == 'hidden_incog_input_params':
				check_infile(fn,blkdev_ok=True)
				key2 = 'in_fmt'
			else:
				try: os.stat(fn)
				except:
					b = os.path.dirname(fn)
					if b: check_outdir(b)
				else: check_outfile(fn,blkdev_ok=True)
				key2 = 'out_fmt'
			if hasattr(opt,key2):
				val2 = getattr(opt,key2)
				from mmgen.seed import IncogWalletHidden
				if val2 and val2 not in IncogWalletHidden.fmt_codes:
					die(1,
						'Option conflict:\n  %s, with\n  %s=%s' % (
						fmt_opt(key),fmt_opt(key2),val2
					))
		elif key == 'seed_len':
			if not opt_is_int(val,desc): return False
			if not opt_is_in_list(int(val),g.seed_lens,desc): return False
		elif key == 'hash_preset':
			if not opt_is_in_list(val,g.hash_presets.keys(),desc): return False
		elif key == 'brain_params':
			a = val.split(',')
			if len(a) != 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			d = 'seed length ' + desc
			if not opt_is_int(a[0],d): return False
			if not opt_is_in_list(int(a[0]),g.seed_lens,d): return False
			d = 'hash preset ' + desc
			if not opt_is_in_list(a[1],g.hash_presets.keys(),d): return False
		elif key == 'usr_randchars':
			if val == 0: continue
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,'>=',g.min_urandchars,desc): return False
			if not opt_compares(val,'<=',g.max_urandchars,desc): return False
		elif key == 'tx_fee':
			if not opt_is_tx_fee(val,desc): return False
		elif key == 'tx_confs':
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,'>=',1,desc): return False
		elif key == 'key_generator':
			if not opt_compares(val,'<=',len(g.key_generators),desc): return False
			if not opt_compares(val,'>',0,desc): return False
		elif key == 'coin':
			if not opt_is_in_list(val.upper(),g.coins,'coin'): return False
		else:
			if g.debug: Msg("check_opts(): No test for opt '%s'" % key)

	return True
