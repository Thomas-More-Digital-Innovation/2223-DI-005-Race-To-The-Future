obj-m += shooterdriver.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD)

modules_install:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules_install

clean:
	rm -f *.o *~ core .depend .*.cmd *.ko *.mod.c *.mod
	rm -f Module.markers Module.symvers modules.order
	rm -rf .tmp_versions Modules.symvers