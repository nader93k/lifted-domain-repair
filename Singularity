# Build the container, install dependencies
Bootstrap: docker
From: ubuntu:20.04

%environment
    # TODO: in case we need to specify variables here
    export TODO=/path 

%files
    ## Copy current folder (== 'porject dir') to /repair-project
    . /repair-project

%post
    export DEBIAN_FRONTEND=noninteractive

    # install standard build/python tools
    apt-get update
    apt-get -y install --no-install-recommends \
               wget \
               p7zip-full \
               python3.8 \
               python3.8-venv \
               python3.8-distutils \
               python3-pip \
               cmake \
               g++ \
               make \
               build-essential \
               autotools-dev \
               libboost-all-dev \
               libboost-program-options-dev

    # isntall python dependencies
    python3.8 -m pip install 'python-sat[aiger,approxmc,cryptosat,pblib]'
    python3.8 -m pip install tarski==0.4.0

    # install lpopt
    wget https://dbai.tuwien.ac.at/proj/lpopt/lpopt-2.2-x86_64.tar.gz
    tar -xvzf lpopt-2.2-x86_64.tar.gz
    mv lpopt-2.2-x86_64/* /usr/bin/
    rm lpopt-2.2-x86_64.tar.gz

    # install htd
    wget https://github.com/mabseher/htd/archive/refs/tags/1.2.zip -O htd-1.2.zip
    7z x htd-1.2.zip -ohtd-1.2
    cd htd-1.2
    cd htd-1.2
    mkdir build && cd build
    cmake ..
    make -j8
    make install
    cd ../..
    rm -rf htd-1.2.zip

    # compile local sources
    #cd /repair-project
    #cd relaxation_generator
    #python3 build.py
    #cd ../fd2
    #python3 build.py
    #cd ../pwl
    #python3 build.py


%runscript
    #TODO: should be set to whatever we actually want to run
    python3.8 /repair-project/debug.py
