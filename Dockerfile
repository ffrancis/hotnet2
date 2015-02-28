# Docker Container for Basic HotNet2 Setup
FROM continuumio/miniconda

MAINTAINER Keiichiro Ono <kono@ucsd.edu> 

RUN apt-get update && apt-get install -y g++ make cmake
RUN conda update conda && conda update anaconda
RUN conda install scipy numpy networkx

WORKDIR /
RUN mkdir hotnet2

WORKDIR /hotnet2

ADD . /hotnet2

RUN python hotnet2/setup_c.py build_src build_ext --inplace

#RUN python makeRequiredPPRFiles.py @influence_matrices/hprd.config
#RUN python makeRequiredPPRFiles.py @influence_matrices/irefindex.config