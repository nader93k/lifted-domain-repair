# Build the container, install dependencies
Bootstrap: docker
From: ubuntu:22.04

%environment
    # TODO: in case we need to specify variables here
    export TODO=/path 

%files
    ## Copy current folder (== 'porject dir') to /repair-project
    . /repair-project

%post
    # install standard build/python tools
    apt-get update
    apt-get -y install --no-install-recommends \
               python3.9 \
               python3.9-venv \
               cmake \
               g++ \
               make \
               build-essential \
               autotools-dev \
               libboost-all-dev=1.74.0.3ubuntu7 \
               libboost-program-options1.74-dev

    # isntall python dependencies
    pip install 'python-sat[aiger,approxmc,cryptosat,pblib]'
    pip install tarski==0.4.0

    # install lpopt
    wget https://dbai.tuwien.ac.at/proj/lpopt/lpopt-2.2-x86_64.tar.gz
    tar -xvzf lpopt-2.2-x86_64.tar.gz
    sudo mv lpopt-2.2-x86_64/* /usr/bin/
    rm lpopt-2.2-x86_64.tar.gz

    # install htd
    wget https://github.com/mabseher/htd/archive/refs/tags/1.2.zip -O htd-1.2.zip
    unzip htd-1.2.zip
    cd htd-1.2
    mkdir build && cd build
    cmake ..
    make
    sudo make install
    cd ../..
    rm -rf htd-1.2 htd-1.2.zip

    # compile local sources
    cd /repair-project
    cd relaxation_generator
    python3 build.py
    cd ../fd2
    python3 build.py
    cd ../pwl
    python3 build.py


%runscript
    #TODO: should be set to whatever we actually want to run
    python3 debug.py
