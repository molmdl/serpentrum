#!/bin/bash
CWD=`pwd`
cd tmp/xtb_test
${CWD}/xtb-6.7.1/bin/xtb.exe phenol.xyz --ohess > phenol_ohess.log 2>&1
