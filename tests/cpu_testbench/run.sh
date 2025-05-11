#!/usr/bin/env bash

kernel_asm=$1
cp "$kernel_asm" ./kernel.s
make -s qemu
