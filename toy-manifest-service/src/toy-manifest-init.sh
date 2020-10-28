#!/bin/sh -x

CWD=`pwd`
cd /sqitch/bundle
sqitch deploy toy_manifest_db
cd $CWD
