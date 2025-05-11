CROSS=riscv64-unknown-elf-
GCC=${CROSS}gcc
AS=${CROSS}as
LD=${CROSS}ld
OPTS=-march=rv64imzicsr -mabi=lp64
COPTS=${OPTS} -mcmodel=medany -static -nostdlib -nostartfiles -fvisibility=hidden

clean:
	rm -rf build/kernel build/*.{o,s}

build/stdlib.o: stdlib.c
	$(GCC) $(COPTS) -w -o $@ -c $^

build/kernel.o: kernel.s
	$(AS) $(OPTS) -o $@ $^

build/kernel: kernel.ld build/kernel.o build/stdlib.o
	$(LD) \
		-w -Tkernel.ld -o $@ \
		build/kernel.o build/stdlib.o &>/dev/null

qemu: build/kernel
	qemu-system-riscv64 \
		-machine sifive_u \
		-nographic -bios none \
		-kernel $<

.PHONY: clean qemu
