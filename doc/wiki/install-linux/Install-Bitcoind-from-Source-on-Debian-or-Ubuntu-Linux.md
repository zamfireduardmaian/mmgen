Make sure that the following development packages for the boost library are
installed (package names may vary; the version should be 1.48 or greater, and
version 1.54 on Ubuntu 13.10 is reported not to work):

		libboost-system-dev
		libboost-filesystem-dev
		libboost-program-options-dev
		libboost-chrono-dev
		libboost-test-dev
		libboost-thread-dev

You'll also need the standard build tools if they're not already on your system:

		sudo apt-get install build-essential libtool autotools-dev autoconf pkg-config libssl-dev


Clone the bitcoin repository from Github, configure, and build:

		$ git clone https://github.com/bitcoin/bitcoin.git
		$ cd bitcoin
		$ ./autogen.sh
		$ ./configure --without-gui
		$ make -j4

If 'configure' complains about a missing libdb version 4.8, you have two
options: either install the libdb4.8-dev and libdb4.8++-dev packages (you may
have to obtain them from elsewhere) or install your distribution's current
libdbX.X-dev and libdbX.X++-dev packages and add the '--with-incompatible-bdb'
option to the 'configure' command line.  Be warned that the latter option will
result in your 'wallet.dat' files being incompatible with the prebuilt binary
version of bitcoind.

For more detailed information on this and other dependency issues, consult the
file 'doc/build-unix.md' in the bitcoin source repository.

Your freshly compiled daemon is now in the src/ directory.  Refer to **Run:** on
the [binary installation page][01] for running instructions.

[01]: Install-Bitcoind
[dl]: https://bitcoin.org/en/download
[gs]: Getting-Started-with-MMGen
