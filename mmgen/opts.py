#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
import sys

import mmgen.globalvars as g
import mmgen.share.Opts
import opt
from mmgen.util import msg,msg_r,mdie,mmsg,Msg,die,is_mmgen_wallet_label

def usage():
	Msg("USAGE: %s %s" % (g.prog_name, usage_txt))
	sys.exit(2)

def print_version_info():
	Msg("""
{pgnm_uc} version {g.version}
Part of the {pnm} suite, a Bitcoin cold-storage solution for the com-
mand line.   Copyright (C) {g.Cdates} {g.author} {g.email}
""".format(pnm=g.proj_name, g=g, pgnm_uc=g.prog_name.upper()).strip())

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in group]
		if len(bad) > 1:
			die(1,"Conflicting options: %s" % ", ".join([fmt_opt(b) for b in bad]))

def _typeconvert_from_dfl(key):

	global opt

	gval = g.__dict__[key]
	uval = opt.__dict__[key]
	gtype = type(gval)

	try:
		opt.__dict__[key] = gtype(opt.__dict__[key])
	except:
		d = {
			'int':   'an integer',
			'str':   'a string',
			'float': 'a float',
			'bool':  'a boolean value',
		}
		die(1, "'%s': invalid parameter for '--%s' option (not %s)" % (
			opt.__dict__[key],
			key.replace("_","-"),
			d[gtype.__name__]
		))

	if g.debug:
		Msg("Opt overriden by user:\n    %-18s: %s" % (
				key, ("%s -> %s" % (gval,uval))
			))

def fmt_opt(o): return "--" + o.replace("_","-")

def _show_hash_presets():
	fs = "  {:<7} {:<6} {:<3}  {}"
	msg("Available parameters for scrypt.hash():")
	msg(fs.format("Preset","N","r","p"))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format("'%s'" % i, *g.hash_presets[i]))
	msg("N = memory usage (power of two), p = iterations (rounds)")

def init(opts_data,add_opts=[],opt_filter=None):

	if len(sys.argv) == 2 and sys.argv[1] == '--version':
		print_version_info(); sys.exit()

	uopts,args,short_opts,long_opts,skipped_opts = \
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter)

	if g.debug:
		d = (
			("Short opts",         short_opts),
			("Long opts",          long_opts),
			("Skipped opts",       skipped_opts),
			("User-selected opts", uopts),
			("Cmd args",           args),
		)
		Msg("\n### BEGIN OPTS.PY ###")
		for e in d: Msg("{:<20}: {}".format(*e))

	# Save this for usage()
	global usage_txt
	usage_txt = opts_data['usage']

	# We don't need this data anymore
	del mmgen.share.Opts
	for k in 'prog_name','desc','usage','options','notes':
		if k in opts_data: del opts_data[k]

	# Remove all unneeded attributes from opt, our special global namespace
	for k in dir(opt):
		if k[:2] == "__": del opt.__dict__[k]

	# Transfer uopts into opt, setting required opts to None if not set by user
	for o in [s.rstrip("=") for s in long_opts] + \
			g.required_opts + add_opts + skipped_opts:
		opt.__dict__[o] = uopts[o] if o in uopts else None

	# A special case - do this here, before opt gets set from g.dfl_vars
	if opt.usr_randchars: g.use_urandchars = True

	# If user opt is set, convert its type based on value in mmgen.globalvars
	# If unset, set it to default value in mmgen.globalvars (g):
	opt.__dict__['set_by_user'] = []
	for k in g.dfl_vars:
		if k in opt.__dict__ and opt.__dict__[k] != None:
			_typeconvert_from_dfl(k)
			opt.set_by_user.append(k)
		else:
			opt.__dict__[k] = g.__dict__[k]

	# Check user-set opts without modifying them
	if not check_opts(uopts): sys.exit(1)

	if opt.show_hash_presets:
		_show_hash_presets(); sys.exit(0)

	if opt.debug: opt.verbose = True

	if g.debug:
		Msg("Opts after processing:")
		for k in opt.__dict__:
			v = opt.__dict__[k]
			if v != None and k != "opts":
				Msg("    %-18s: %-6s [%s]" % (k,v,type(v).__name__))
		Msg("### END OPTS.PY ###\n")

	die_on_incompatible_opts(g.incompatible_opts)

	return args

# save for debugging
def show_all_opts():
	msg("Processed options:")
	d = opt.__dict__
	for k in [o for o in d if o != "opts"]:
		tstr = type(d[k]) if d[k] not in (None,False,True) else ""
		msg("%-20s: %-8s %s" % (k, d[k], tstr))

def check_opts(usr_opts):       # Returns false if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = "comma" if sep == "," else (
					"colon" if sep == ":" else ("'"+sep+"'"))
		try: l = val.split(sep)
		except:
			msg("'%s': invalid %s (not %s-separated list)" % (val,desc,sepword))
			return False

		if len(l) == n: return True
		else:
			msg("'%s': invalid %s (%s %s-separated items required)" %
					(val,desc,n,sepword))
			return False

	def opt_compares(val,op,target,desc):
		if not eval("%s %s %s" % (val, op, target)):
			msg("%s: invalid %s (not %s %s)" % (val,desc,op,target))
			return False
		return True

	def opt_is_int(val,desc):
		try: int(val)
		except:
			msg("'%s': invalid %s (not an integer)" % (val,desc))
			return False
		return True

	def opt_is_in_list(val,lst,desc):
		if val not in lst:
			q,sep = ("'","','") if type(lst[0]) == str else ("",",")
			msg("{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}".format(
					v=val,w=desc,q=q,
					o=sep.join([str(i) for i in sorted(lst)])
				))
			return False
		return True

	def opt_unrecognized(key,val,desc):
		msg("'%s': unrecognized %s for option '%s'"
				% (val,desc,fmt_opt(key)))
		return False

	def opt_display(key,val='',beg="For selected",end=":\n"):
		s = "%s=%s" % (fmt_opt(key),val) if val else fmt_opt(key)
		msg_r("%s option '%s'%s" % (beg,s,end))

	global opt
	for key,val in [(k,getattr(opt,k)) for k in usr_opts]:

		desc = "parameter for '%s' option" % fmt_opt(key)

		# Check for file existence and readability
		from mmgen.util import check_infile
		if key in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			check_infile(val)  # exits on error
			continue

		if key == 'outdir':
			from mmgen.util import check_outdir
			check_outdir(val)  # exits on error
		elif key == 'label':
			if not is_mmgen_wallet_label(val):
				msg("Illegal value for option '%s': '%s'" % (fmt_opt(key),val))
				return False
		# NEW
		elif key in ('in_fmt','out_fmt'):
			from mmgen.seed import SeedSource,IncogWallet,Brainwallet,IncogWalletHidden
			sstype = SeedSource.fmt_code_to_sstype(val)
			if not sstype:
				return opt_unrecognized(key,val,"format code")
			if key == 'out_fmt':
				p = 'hidden_incog_output_params'
				if sstype == IncogWalletHidden and not getattr(opt,p):
						die(1,"Hidden incog format output requested. You must supply"
						+ " a file and offset with the '%s' option" % fmt_opt(p))
				if issubclass(sstype,IncogWallet) and opt.old_incog_fmt:
					opt_display(key,val,beg="Selected",end=" ")
					opt_display('old_incog_fmt',beg="conflicts with",end=":\n")
					die(1,"Export to old incog wallet format unsupported")
				elif issubclass(sstype,Brainwallet):
					die(1,"Output to brainwallet format unsupported")
		elif key in ('hidden_incog_input_params','hidden_incog_output_params'):
			if key == 'hidden_incog_input_params':
				check_infile(val.split(",")[0])
				key2 = 'in_fmt'
			else:
				key2 = 'out_fmt'
			if hasattr(opt,key2):
				val2 = getattr(opt,key2)
				from mmgen.seed import IncogWalletHidden
				if val2 and val2 not in IncogWalletHidden.fmt_codes:
					die(1,
						"Option conflict:\n  %s, with\n  %s=%s" % (
						fmt_opt(key),fmt_opt(key2),val2
					))

		# begin OLD, deprecated
		elif key == 'hidden_incog_params':
			from mmgen.util import check_outfile
			if not opt_splits(val,",",2,desc): return False
			outfile,offset = val.split(",")
			check_outfile(outfile)
			w = "offset " + desc
			if not opt_is_int(offset,w): return False
			if not opt_compares(offset,">=",0,desc): return False
		elif key == 'export_incog_hidden' or key == 'from_incog_hidden':
			if key == 'from_incog_hidden':
				if not opt_splits(val,",",3,desc): return False
				infile,offset,seed_len = val.split(",")
				from mmgen.util import check_infile
				check_infile(infile)
				w = "seed length " + desc
				if not opt_is_int(seed_len,w): return False
				if not opt_is_in_list(int(seed_len),g.seed_lens,w): return False
			else:
				from mmgen.util import check_outfile
				if not opt_splits(val,",",2,desc): return False
				outfile,offset = val.split(",")
				check_outfile(outfile)
			w = "offset " + desc
			if not opt_is_int(offset,w): return False
			if not opt_compares(offset,">=",0,desc): return False
		elif key == 'from_brain':
			if not opt_splits(val,",",2,desc): return False
			l,p = val.split(",")
			w = "seed length " + desc
			if not opt_is_int(l,w): return False
			if not opt_is_in_list(int(l),g.seed_lens,w): return False
			w = "hash preset " + desc
			if not opt_is_in_list(p,g.hash_presets.keys(),w): return False
		# end OLD
		elif key == 'seed_len':
			if not opt_is_int(val,desc): return False
			if not opt_is_in_list(int(val),g.seed_lens,desc): return False
		elif key == 'hash_preset':
			if not opt_is_in_list(val,g.hash_presets.keys(),desc): return False
		elif key == 'usr_randchars':
			if val == 0: continue
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,">=",g.min_urandchars,desc): return False
			if not opt_compares(val,"<=",g.max_urandchars,desc): return False
		else:
			if g.debug: Msg("check_opts(): No test for opt '%s'" % key)

	return True
