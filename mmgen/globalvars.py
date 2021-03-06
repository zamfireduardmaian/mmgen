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
globalvars.py:  Constants and configuration options for the MMGen suite
"""

import sys,os
from mmgen.obj import BTCAmt

# Global vars are set to dfl values in class g.
# They're overridden in this order:
#   1 - config file
#   2 - environmental vars
#   3 - command line

class g(object):

	skip_segwit_active_check = bool(os.getenv('MMGEN_TEST_SUITE'))

	def die(ev=0,s=''):
		if s: sys.stderr.write(s+'\n')
		sys.exit(ev)
	# Variables - these might be altered at runtime:

	version      = '0.9.299'
	release_date = 'July 2017'

	proj_name = 'MMGen'
	proj_url  = 'https://github.com/mmgen/mmgen'
	prog_name = os.path.basename(sys.argv[0])
	author    = 'Philemon'
	email     = '<mmgen@tuta.io>'
	Cdates    = '2013-2017'
	keywords  = 'Bitcoin, cryptocurrency, wallet, cold storage, offline, online, spending, open-source, command-line, Python, Bitcoin Core, bitcoind, hd, deterministic, hierarchical, secure, anonymous, Electrum, seed, mnemonic, brainwallet, Scrypt, utility, script, scriptable, blockchain, raw, transaction, permissionless, console, terminal, curses, ansi, color, tmux, remote, client, daemon, RPC, json, entropy, xterm, rxvt, PowerShell, MSYS, MinGW, mswin'

	coin   = 'BTC'
	coins  = 'BTC','BCH'
	ports = { 'BTC': (8332,18332), 'BCH': (8442,18442) }

	user_entropy   = ''
	hash_preset    = '3'
	usr_randchars  = 30
	stdin_tty      = bool(sys.stdin.isatty() or os.getenv('MMGEN_TEST_SUITE'))

	max_tx_fee   = BTCAmt('0.01')
	tx_fee_adj   = 1.0
	tx_confs     = 3
	satoshi      = BTCAmt('0.00000001') # One bitcoin equals 100,000,000 satoshis
	seed_len     = 256

	http_timeout = 60
	max_int      = 0xffffffff

	# Constants - some of these might be overriden, but they don't change thereafter

	debug                = False
	quiet                = False
	no_license           = False
	hold_protect         = True
	color                = (False,True)[sys.stdout.isatty()]
	force_256_color      = False
	testnet              = False
	regtest              = False
	chain                = None # set by first call to bitcoin_connection()
	chains               = 'mainnet','testnet','regtest'
	bitcoind_version     = None # set by first call to bitcoin_connection()
	rpc_host             = ''
	rpc_port             = 0
	rpc_user             = ''
	rpc_password         = ''
	testnet_name         = 'testnet3'

	bob                  = False
	alice                = False

	# test suite:
	bogus_wallet_data    = ''
	traceback_cmd        = 'scripts/traceback.py'

	for k in ('win','linux'):
		if sys.platform[:len(k)] == k:
			platform = k; break
	else:
		die(1,"'%s': platform not supported by %s\n" % (sys.platform,proj_name))

	if os.getenv('HOME'):                             # Linux or MSYS
		home_dir = os.getenv('HOME')
	elif platform == 'win': # Windows native:
		die(1,'$HOME not set!  {} for Windows must be run in MSYS environment'.format(proj_name))
	else:
		die(2,'$HOME is not set!  Unable to determine home directory')

	data_dir_root,data_dir,cfg_file = None,None,None
	bitcoin_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin') if platform == 'win' \
						else os.path.join(home_dir,'.bitcoin')

	# User opt sets global var:
	common_opts = (
		'color','no_license','rpc_host','rpc_port','testnet','rpc_user','rpc_password',
		'bitcoin_data_dir','force_256_color','regtest','coin','bob','alice'
	)
	required_opts = (
		'quiet','verbose','debug','outdir','echo_passphrase','passwd_file','stdout',
		'show_hash_presets','label','keep_passphrase','keep_hash_preset','yes',
		'brain_params','b16','usr_randchars','coin','bob','alice'
	)
	incompatible_opts = (
		('bob','alice'),
		('quiet','verbose'),
		('label','keep_label'),
		('tx_id','info'),
		('tx_id','terse_info'),
		('aug1hf','rbf'), # TODO: remove in 0.9.4
		('batch','rescan')
	)
	cfg_file_opts = (
		'color','debug','hash_preset','http_timeout','no_license','rpc_host','rpc_port',
		'quiet','tx_fee_adj','usr_randchars','testnet','rpc_user','rpc_password',
		'bitcoin_data_dir','force_256_color','max_tx_fee','regtest'
	)
	env_opts = (
		'MMGEN_BOGUS_WALLET_DATA',
		'MMGEN_DEBUG',
		'MMGEN_QUIET',
		'MMGEN_DISABLE_COLOR',
		'MMGEN_FORCE_256_COLOR',
		'MMGEN_DISABLE_HOLD_PROTECT',
		'MMGEN_MIN_URANDCHARS',
		'MMGEN_NO_LICENSE',
		'MMGEN_RPC_HOST',
		'MMGEN_TESTNET'
		'MMGEN_REGTEST'
	)

	min_screen_width = 80
	minconf = 1

	# Global var sets user opt:
	global_sets_opt = ['minconf','seed_len','hash_preset','usr_randchars','debug',
						'quiet','tx_confs','tx_fee_adj','key_generator']

	mins_per_block   = 9
	passwd_max_tries = 5

	max_urandchars = 80
	min_urandchars = 10

	seed_lens = 128,192,256

	mmenc_ext      = 'mmenc'
	salt_len       = 16
	aesctr_iv_len  = 16
	hincog_chk_len = 8

	key_generators = 'python-ecdsa','secp256k1' # '1','2'
	key_generator  = 2 # secp256k1 is default

	hash_presets = {
#   Scrypt params:
#   ID    N   p  r
# N is a power of two
		'1': [12, 8, 1],
		'2': [13, 8, 4],
		'3': [14, 8, 8],
		'4': [15, 8, 12],
		'5': [16, 8, 16],
		'6': [17, 8, 20],
		'7': [18, 8, 24],
	}
