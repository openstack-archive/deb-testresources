PYTHONPATH:=$(shell pwd)/lib:${PYTHONPATH}

all:

check:
	PYTHONPATH=$(PYTHONPATH) python ./test_all.py $(TESTRULE)

clean:
	find . -name '*.pyc' -print0 | xargs -0 rm -f

.PHONY: all check clean
