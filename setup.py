#  Copyright (c) 2015 SONATA-NFV, 5GTANGO, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

from setuptools import setup, find_packages
import os.path as path

cwd = path.dirname(__file__)
with open(path.join(cwd, 'requirements.txt')) as f:
    requirements = f.read().splitlines()


def install_deps():
    """
    Workaround to load GitHub-hosted Python packages
    from requirements.txt.
    see: https://github.com/pypa/pip/issues/3610#issuecomment-356687173
    """
    with open(path.join(cwd, 'requirements.txt')) as f:
        requirements = f.read().splitlines()
        new_pkgs = []
        links = []
        for r in requirements:
            if "https" in r:
                pkg = r.split('#')[-1]
                links.append(r.strip())
                new_pkgs.append(pkg.replace('egg=', '').rstrip())
            else:
                new_pkgs.append(r.strip())
        return new_pkgs, links


longdesc = """
Component to automatically benchmark network services
and VNFs.
"""

# load dependencies
pkgs, new_links = install_deps()

setup(name='tngsdk.benchmark',
      license='Apache License, Version 2.0',
      version='5.0',
      url='https://github.com/sonata-nfv/tng-sdk-benchmark',
      author='Manuel Peuster',
      author_email='manuel.peuster@uni-paderborn.de',
      long_description=longdesc,
      package_dir={'': 'src'},
      packages=find_packages('src'),  # dependency resolution
      namespace_packages=['tngsdk', ],
      include_package_data=True,       # package data specified in MANIFEST.in
      install_requires=pkgs,
      dependency_links=new_links,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              # default benchmarker entry points
              'tng-sdk-benchmark=tngsdk.benchmark:main',
              'tng-benchmark=tngsdk.benchmark:main',
              'tng-bench=tngsdk.benchmark:main',
              # processing of existing results
              'tng-bench-result=tngsdk.benchmark:main_result_processor',
              # vim-emu server component (python2!)
              'tng-bench-emusrv=tngsdk.benchmark.pdriver.vimemu.server:main'
          ],
      },
      test_suite='tngsdk',
      setup_requires=[],
      tests_require=['pytest'])
