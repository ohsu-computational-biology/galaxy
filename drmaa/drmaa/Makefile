CC=gcc
SO=.so
DEBUG=-g  
LDSHARED=$(CC) -shared $(LDFLAGS)
CFLAGS=-g -O2  -DHAVE_CONFIG_H -I. -fPIC -Wall
OBJS= libDrmaa.o auxDrmaa.o drmaa_common.o iniparser.o

all : libdrmaa$(SO) libcondordrmaa.a

auxDrmaa.o: drmaa_common.o auxDrmaa.c auxDrmaa.h iniparser.o 
	$(CC) $(DEBUG) -c $(CFLAGS) -DSYSCONFDIR=\"${prefix}/etc\" auxDrmaa.c -o auxDrmaa.o

libDrmaa.o: drmaa_common.o auxDrmaa.o libDrmaa.c drmaa.h
	$(CC) $(DEBUG) -c $(CFLAGS) -DSYSCONFDIR=\"${prefix}/etc\" libDrmaa.c -o libDrmaa.o

drmaa_common.o: drmaa_common.h drmaa_common.c
	$(CC) $(DEBUG) -c $(CFLAGS) drmaa_common.c -o drmaa_common.o

iniparser.o: iniparser.h iniparser.c
	$(CC) $(DEBUG) -c $(CFLAGS) iniparser.c -o iniparser.o

libdrmaa$(SO): $(OBJS)
	$(LDSHARED) $(DEBUG) -o $@ $(OBJS) -lpthread

libcondordrmaa.a: $(OBJS) 
	/usr/bin/ar vr $@ $(OBJS)

test_drmaa: libdrmaa$(SO) test/test_drmaa.c test_exit_helper test_kill_helper
	$(CC) $(DEBUG) $(CFLAGS) -o $@ test/test_drmaa.c -L. -ldrmaa

test_exit_helper: test/test_exit_helper.c
	$(CC) $(DEBUG) $(CFLAGS) -o $@ test/test_exit_helper.c 

test_kill_helper: test/test_kill_helper.c
	$(CC) $(DEBUG) $(CFLAGS) -o $@ test/test_kill_helper.c 

clean:
	rm -f *$(SO) *.o test_drmaa test_exit_helper test_kill_helper *.a *~ config.log 
	rm -rf autom4te.cache

srcdist:
	tar cvfz drmaa_src.tgz ../drmaa/*.c ../drmaa/*.h ../drmaa/WISDOM ../drmaa/STATUS ../drmaa/README ../drmaa/Makefile.in ../drmaa/config.h.in ../drmaa/configure ../drmaa/configure.in ../drmaa/documentation

distclean: clean
	rm -f config.h config.status Makefile
