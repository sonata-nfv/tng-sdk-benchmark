[![Join the chat at https://gitter.im/sonata-nfv/Lobby](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/sonata-nfv/Lobby)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# 5GTANGO VNF/NS Benchmarking Framework

This repository contains the `tng-sdk-benchmark` component that is part of the European H2020 project [5GTANGO](http://www.5gtango.eu) NFV SDK. This component is responsible to automatically execute performance benchmarks of NFV network services and functions.

The seed code of this component is based on the `son-cli` toolbox, specifically the `son-profile` tool, which was developed as part of the European H2020 project [SONATA](http://sonata-nfv.eu).

## Cite this Work

If you use this tool for your research, publications, or NFV projects, please consider to cite the following paper(s):

* M. Peuster and H. Karl: [Profile Your Chains, Not Functions: Automated Network Service Profiling in DevOps Environments](http://ieeexplore.ieee.org/document/8169826/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Berlin, Germany. (2017)

* M. Peuster, H. Karl: [Understand Your Chains: Towards Performance Profile-based Network Service Management](http://ieeexplore.ieee.org/document/7956044/). Fifth European Workshop on Software Defined Networks (EWSDN). IEEE. (2016)

* M. Peuster, H. Karl, and S. v. Rossem: [MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments](http://ieeexplore.ieee.org/document/7919490/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, pp. 148-153. doi: 10.1109/NFV-SDN.2016.7919490. (2016)


## Installation

Please follow [this guide](https://github.com/sonata-nfv/tng-sdk-benchmark/wiki/Setup-execution-platform-(vim-emu)) to install and setup tng-sdk-benchmark and a corresponding execution environment.

## Usage

### Run a benchmarking experiment

Before you can run your first benchmarking experiment, you need to install tng-bench and an execution platform following [this guide](https://github.com/sonata-nfv/tng-sdk-benchmark/wiki/Setup-execution-platform-(vim-emu)).

```sh
tng-bench -p examples/peds/ped_suricata_tp_small.yml
```

### Manually re-run the result processing

Runs the result processing module using existing results. This step is also automatically performed once at the end of an experiment execution.

```sh
# manually trigger result processing of generated results (to create *.csv files)
tng-bench-result -rd results/  
```


## Development

To contribute to the development of this 5GTANGO component, you may use the very same development workflow as for any other 5GTANGO Github project. That is, you have to fork the repository and create pull requests.

### Setup development environment

```bash
$ python setup.py develop
```

### CI Integration

All pull requests are automatically tested by Jenkins and will only be accepted if no test is broken.

### Run tests manually

You can also run the test manually on your local machine. To do so, you need to do:

```bash
$ pytest -v
```

## License

This 5GTANGO component is published under Apache 2.0 license. Please see the LICENSE file for more details.

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

- Manuel Peuster ([@mpeuster](https://github.com/mpeuster))
- Stefan Schneider ([@StefanUPB](https://github.com/StefanUPB))

#### Feedback-Chanel

* Please use the GitHub issues to report bugs.
